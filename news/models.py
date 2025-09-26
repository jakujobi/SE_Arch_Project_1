"""
news/models.py

Lean data model for the class MVP:
- Source 1..* Article
- User 1..1 UserProfile  (tier: free | standard | premium)
- User 1..* ReadEvent    (per-day metering for logged-in users)
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Source(models.Model):
    #External content source (RSS for MVP).
    #Admins can disable a feed without deleting rows by toggling `enabled`.

    TYPE_CHOICES = [
        ("rss", "RSS"),
        ("hacker_news", "Hacker News"),
        ("guardian", "The Guardian"),
    ]

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="rss")
    url = models.URLField(max_length=500)
    enabled = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["enabled"], name="idx_source_enabled"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"


class Article(models.Model):
    #Normalized article we list and link out to (snippet + external link).
    #JSON-like fields are stored as TEXT to stay SQLite-friendly.

    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="articles")

    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    summary = models.TextField(blank=True, null=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True)

    # Store timestamps in UTC; convert in views if needed.
    published_at = models.DateTimeField(blank=True, null=True)
    ingested_at = models.DateTimeField(default=timezone.now)

    # JSON-encoded lists (e.g., '["AI","Gadgets"]'); keep as TEXT for SQLite.
    tags = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)

    # Dedup key computed by the ingest command: sha256(canonical_link or link or title).
    hash = models.CharField(max_length=64, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["-published_at"], name="idx_article_pub_desc"),
            models.Index(fields=["title"], name="idx_article_title"),
        ]

    def __str__(self) -> str:
        return self.title


class ReadEvent(models.Model):
    #Logged-in metering record. One record per (user, article, local day).
    #Anonymous metering is cookie-based and not stored here.

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="read_events"
    )
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="read_events"
    )

    # Local day (e.g., America/Chicago) computed at request time.
    date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            # Prevent double counting (refresh/multiple tabs).
            models.UniqueConstraint(
                fields=["user", "article", "date"], name="uq_read_once_per_day"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "date"], name="idx_reads_user_date"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} read {self.article_id} on {self.date}"
