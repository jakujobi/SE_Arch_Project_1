# news/management/commands/ingest_news.py
"""
Custom management command to ingest news from RSS feeds.

This command is designed to be safe, reliable, and idempotent.
- Uses a file-based lock to prevent concurrent execution.
- Seeds the Source table from settings.FEEDS on first run.
- Fetches from enabled sources only.
- Handles network errors and malformed feed data gracefully on a per-source basis.
- Deduplicates articles using a SHA256 hash of the article link.
"""

import hashlib
import feedparser
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from dateutil.parser import parse as parse_datetime

from news.models import Article, Source


class Command(BaseCommand):
    help = "Fetches and ingests news articles from enabled RSS feeds."

    def handle(self, *args, **options):
        # 1. --- Concurrency Lock ---
        # Ensure only one instance of the command runs at a time.
        lock_file = Path(settings.BASE_DIR) / "ingest_news.lock"
        if lock_file.exists():
            raise CommandError("Ingestion command is already running. If this is an error, delete the .lock file.")
        
        try:
            lock_file.touch()
            self.stdout.write(self.style.SUCCESS("Successfully acquired lock file."))

            # 2. --- Seed Sources ---
            # Ensure the Source table has entries matching settings.FEEDS
            self._seed_sources()

            # 3. --- Main Ingestion Logic ---
            self._fetch_and_process_feeds()

        finally:
            # 4. --- Release Lock ---
            # Guarantees the lock file is removed, even if errors occur.
            lock_file.unlink()
            self.stdout.write(self.style.SUCCESS("Lock file released. Ingestion finished."))

    def _seed_sources(self):
        """Ensures the database has a Source object for each URL in settings."""
        self.stdout.write("Seeding sources from settings...")
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
                self.stdout.write(self.style.SUCCESS(f"  + Created source: {source.name}"))
        
        if seeded_count > 0:
            self.stdout.write(f"{seeded_count} new sources were added to the database.")
        else:
            self.stdout.write("All sources from settings already existed in the database.")


    def _fetch_and_process_feeds(self):
        """Fetches content from all enabled sources and processes their articles."""
        enabled_sources = Source.objects.filter(enabled=True)
        self.stdout.write(f"\nFound {enabled_sources.count()} enabled sources to fetch.")

        for source in enabled_sources:
            self.stdout.write(f"\n--- Fetching from: {source.name} ---")
            try:
                # Use a timeout to prevent the command from hanging indefinitely.
                # Note: feedparser doesn't have a direct timeout, this would be
                # better with 'requests', but for MVP we stick to the plan.
                feed = feedparser.parse(source.url)
                
                if feed.bozo:
                    # bozo is true if the feed is malformed.
                    raise ValueError(f"Feed is malformed. Bozo reason: {feed.bozo_exception}")

                for entry in feed.entries:
                    self._process_entry(source, entry)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing {source.name}: {e}"))
                # The loop continues to the next source.

    def _process_entry(self, source, entry):
        """Processes a single entry from an RSS feed and upserts it to the database."""
        # --- Defensive Data Parsing ---
        if not hasattr(entry, 'link'):
            self.stdout.write(self.style.WARNING("  - Skipping entry with no link."))
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
                self.stdout.write(self.style.WARNING(f"  ? Could not parse date: {entry.get('published')}"))
        
        # --- Database Upsert ---
        article, created = Article.objects.update_or_create(
            hash=dedup_hash,
            defaults={
                'source': source,
                'title': entry.get('title', 'No Title Provided'),
                'url': entry.link,
                'summary': entry.get('summary', ''),
                'published_at': published_time,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"  + Created: {article.title[:60]}..."))
        else:
            # You could add more logic here to check if the update was meaningful
            self.stdout.write(f"  = Exists: {article.title[:60]}...")
