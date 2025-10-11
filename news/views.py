from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import hashlib
import feedparser
from pathlib import Path
from dateutil.parser import parse as parse_datetime
from abc import abstractmethod, ABC

from .models import Article, Source

#Interface
class IGetContent(ABC):
    @abstractmethod
    def get_content(self, request):
        pass


#Concrete base component
class SimpleFetchContent(IGetContent):
    def get_content(self, request):
        # 1. --- Concurrency Lock ---
        # Ensure only one instance of the command runs at a time.
        lock_file = Path(settings.BASE_DIR) / "ingest_news.lock"
        if lock_file.exists():
            raise Exception("Ingestion command is already running. If this is an error, delete the .lock file.")
        
        try:
            lock_file.touch()
            print("Successfully acquired lock file.")

            # 2. --- Seed Sources ---
            # Ensure the Source table has entries matching settings.FEEDS
            self._seed_sources()

            # 3. --- Main Ingestion Logic ---
            entries = self._fetch_and_process_feeds()

            #make context object for actual pasing
            context = {
                'entries': entries
            }
            return context

        finally:
            # 4. --- Release Lock ---
            # Guarantees the lock file is removed, even if errors occur.
            lock_file.unlink()
            print("Lock file released. Ingestion finished.")

    def _seed_sources(self):
        """Ensures the database has a Source object for each URL in settings."""
        print("Seeding sources from settings...")
        seeded_count = 0
        for feed_url in settings.FEEDS:
            # get_or_create is idempotent and safe to run multiple times.
            source, created = Source.objects.get_or_create(
                url=feed_url,
                defaults={
                    "name": feed_url.split("//")[-1].split("/")[0],  # Best-effort name
                    "type": "rss",
                    "enabled": True,
                },
            )
            if created:
                seeded_count += 1
                print(f"  + Created source: {source.name}")
        
        if seeded_count > 0:
            print(f"{seeded_count} new sources were added to the database.")
        else:
            print("All sources from settings already existed in the database.")

    def _fetch_and_process_feeds(self):
        entries = []

        #Fetches content from all enabled sources and processes their articles.
        enabled_sources = Source.objects.filter(enabled=True)
        print(f"\nFound {enabled_sources.count()} enabled sources to fetch.")

        for source in enabled_sources:
            print(f"\n--- Fetching from: {source.name} ---")
            try:
                # Use a timeout to prevent the command from hanging indefinitely.
                # Note: feedparser doesn't have a direct timeout, this would be
                # better with 'requests', but for MVP we stick to the plan.
                feed = feedparser.parse(source.url)
                
                if feed.bozo:
                    # bozo is true if the feed is malformed.
                    raise ValueError(f"Feed is malformed. Bozo reason: {feed.bozo_exception}")

                for entry in feed.entries:
                    parsed = self._process_entry(source, entry)
                    if parsed:
                        entries.append(parsed)

            except Exception as e:
                print(f"Error processing {source.name}: {e}")
                # The loop continues to the next source.
            
        return entries

    def _process_entry(self, source, entry):
        #Processes a single entry from an RSS feed passes it back up.
        # --- Defensive Data Parsing ---
        if not hasattr(entry, 'link'):
            print("  - Skipping entry with no link.")
            return
        
        # --- Deduplication ---
        hash_input = entry.link.encode('utf-8')
        dedup_hash = hashlib.sha256(hash_input).hexdigest()

        # --- Date Normalization ---
        published_time = timezone.now()  # Default to now
        if hasattr(entry, 'published'):
            try:
                dt = parse_datetime(entry.published)
                if timezone.is_naive(dt):
                    # Assume the feed's timezone is the project's default timezone
                    published_time = timezone.make_aware(dt, timezone.get_default_timezone())
                else:
                    # It's already aware, just use it
                    published_time = dt
            except (TypeError, ValueError):
                print(f"  ? Could not parse date: {entry.get('published')}")
        
        # --- Database Upsert ---
        return{
            'hash': dedup_hash,
            'source': source,
            'title': entry.get('title', 'No Title Provided'),
            'url': entry.link,
            'summary': entry.get('summary', ''),
            'published_at': published_time,
            'tier': "free"
        }


#Abstract Base Decerator
class ContentDecorator(IGetContent):
    def __init__(self, wrapped: IGetContent):
        self._wrapped = wrapped

    def get_content(self, request):
        return self._wrapped.get_content(request)


#Concrete Decerator
class ContentManagementDec(ContentDecorator):
    def get_content(self, request):
        context = super().get_content(request)
        entries = context.get('entries', []) or []

        # Content filtering while fetching; Articles with "sources" in title are unreliable trash
        filtered_entries = [
            entry for entry in entries
            if "sources" not in entry['title'].lower()
        ]

        # Check for Stale Content
        sorted_entries = sorted(filtered_entries, key=lambda e: e['published_at'], reverse=True)
        is_stale = False
        minutes = settings.TTL_MINUTES
        if sorted_entries:
            latest_article = sorted_entries[0]  # Newest article
            if latest_article['published_at'] < timezone.now() - timedelta(minutes=minutes):
                is_stale = True

        context.update({
            'entries': filtered_entries,
            'is_stale': is_stale,
            'current_tier': None,  # For next decerator
            'minutes': minutes
        })
    
        return context


#Concrete Decerator
class TierDiscriminatorDec(ContentDecorator):
    def get_content(self, request):
        context = super().get_content(request)

        # Fetch and filter articles
        entries = context.get('entries', []) or []
        for entry in entries:
            source_name = entry['source'].name.lower()
            if any(domain in source_name for domain in ["techcrunch.com", "arstechnica.com"]):
                entry['tier'] = "standard"

        # Determine User's Tier;
        if request.user.is_authenticated:
            context['current_tier'] = request.user.profile.get_current_tier() #returns 'Standard' or 'free'
        else:
            context['current_tier'] = "anonymous"

        return context


def home_view(request):
    pipeline = TierDiscriminatorDec(ContentManagementDec(SimpleFetchContent()))
    context = pipeline.get_content(request)

    #Write to DB for faster load times and less API use
    for entry in context.get('entries', []):
        Article.objects.update_or_create(
            hash=entry['hash'],
            defaults=entry
        )

    #Fetch articles from DB for consistency sake
    articles = Article.objects.order_by('-published_at')
    paginator = Paginator(articles, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj

    return render(request, 'news.html', context)


def article_detail_view(request, article_id):
    #Displays the details for a single article with tier-based restrictions.
    article = get_object_or_404(Article, pk=article_id)

    context = {
        'article': article
    }
    return render(request, 'article_detail.html', context)