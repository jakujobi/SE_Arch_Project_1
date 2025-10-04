from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseForbidden
from datetime import timedelta
import hashlib
import feedparser
from pathlib import Path
from dateutil.parser import parse as parse_datetime

from .models import Article, Source

class APIFetch:
    @staticmethod
    def GetContent():
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
            APIFetch._seed_sources()

            # 3. --- Main Ingestion Logic ---
            APIFetch._fetch_and_process_feeds()

        finally:
            # 4. --- Release Lock ---
            # Guarantees the lock file is removed, even if errors occur.
            lock_file.unlink()
            print("Lock file released. Ingestion finished.")

    @staticmethod
    def _seed_sources():
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

    @staticmethod
    def _fetch_and_process_feeds():
        """Fetches content from all enabled sources and processes their articles."""
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
                    APIFetch._process_entry(source, entry)

            except Exception as e:
                print(f"Error processing {source.name}: {e}")
                # The loop continues to the next source.

    @staticmethod
    def _process_entry(source, entry):
        """Processes a single entry from an RSS feed and upserts it to the database."""
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
        article, created = Article.objects.update_or_create(
            hash=dedup_hash,
            defaults={
                'source': source,
                'title': entry.get('title', 'No Title Provided'),
                'url': entry.link,
                'summary': entry.get('summary', ''),
                'published_at': published_time,
                'tier': "free"
            }
        )

        if created:
            print(f"  + Created: {article.title[:60]}...")
        else:
            print(f"  = Exists: {article.title[:60]}...")


class ContentManagement:
    @staticmethod
    def GetConent(request):
        APIFetch.GetContent()

        # Content filtering while fetching; Articles with "sources" in title are unreliable trash
        article_list = Article.objects.exclude(title__icontains="sources").order_by('-published_at')  

        # Paginate Articles
        paginator = Paginator(article_list, 15)  # 15 per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Check for Stale Content
        is_stale = False
        minutes = settings.TTL_MINUTES
        if article_list.exists():
            latest_article = article_list.first()
            if latest_article.ingested_at < timezone.now() - timedelta(minutes=settings.TTL_MINUTES):
                is_stale = True

        return {
            'page_obj': page_obj,
            'is_stale': is_stale,
            'current_tier': None,  # For next class
            'minutes': minutes
        }


class TierDiscriminator:
    @staticmethod
    def GetConent(request):

        context = ContentManagement.GetConent(request)

        # Fetch and filter articles
        sub_articles = Article.objects.filter(source__name__in=["techcrunch.com", "arstechnica.com"])
        for article in sub_articles:
            article.tier = "standard"
            article.save(update_fields=["tier"])

        # Determine User's Tier;
        if request.user.is_authenticated:
            context['current_tier'] = request.user.profile.get_current_tier() #returns 'Standard' or 'free'
        else:
            context['current_tier'] = "anonymous"

        return context


def home_view(request):
    context = TierDiscriminator.GetConent(request)

    return render(request, 'news.html', context)


def article_detail_view(request, article_id):
    #Displays the details for a single article with tier-based restrictions.
    article = get_object_or_404(Article, pk=article_id)

    context = {
        'article': article
    }
    return render(request, 'article_detail.html', context)