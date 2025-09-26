"""
news/admin.py

Admin registration with practical list filters and quick tier actions.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Article, ReadEvent, Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "enabled", "url")
    list_filter = ("type", "enabled")
    search_fields = ("name", "url")
    ordering = ("name",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published_at", "ingested_at")
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


""""
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "tier")
    list_filter = ("tier",)
    search_fields = ("user__username", "user__email")
    actions = ("make_free", "make_standard", "make_premium")

    @admin.action(description="Set selected users to FREE")
    def make_free(self, request, queryset):
        queryset.update(tier="free")

    @admin.action(description="Set selected users to STANDARD")
    def make_standard(self, request, queryset):
        queryset.update(tier="standard")

    @admin.action(description="Set selected users to PREMIUM")
    def make_premium(self, request, queryset):
        queryset.update(tier="premium")
"""


""""
# ----- Optional: Inline profile on the User page (handy for demos) -----

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = "user"
    extra = 0
"""


User = get_user_model()

# Unregister default User admin and re-register with our inline attached.
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


""""
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [UserProfileInline]
"""