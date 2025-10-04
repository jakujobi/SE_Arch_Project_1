"""
news/admin.py

Admin registration with practical list filters and quick tier actions.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Article, ReadEvent, Source

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "enabled", "url")
    list_filter = ("type", "enabled")
    search_fields = ("name", "url")
    ordering = ("name",)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "tier", "published_at", "ingested_at")
    list_filter = ("source",)
    search_fields = ("title", "summary", "url")
    date_hierarchy = "published_at"
    ordering = ("-published_at",)
    readonly_fields = ("ingested_at", "hash")

@admin.register(ReadEvent)
class ReadEventAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "date", "created_at")
    list_filter = ("date",)
    search_fields = ("user__username", "article__title")
    date_hierarchy = "date"
    ordering = ("-date", "-created_at")

User = get_user_model()

# Unregister default User admin and re-register with our inline attached.
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass