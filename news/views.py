from django.shortcuts import render
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Article


def home_view(request):
    """
    Displays the main headlines page with tier-aware content and pagination.
    """
    # 1. --- Determine User's Tier and Content Level ---
    if request.user.is_authenticated:
        # For a logged-in user, use our new method to get their tier.
        current_tier = request.user.profile.get_current_tier()
    else:
        # For an anonymous user, the tier is 'anonymous'.
        current_tier = "anonymous"

    # Look up the content level ('headline' vs 'summary') from TIER_CONFIG.
    tier_config = settings.TIER_CONFIG.get(current_tier, settings.TIER_CONFIG['anonymous'])
    content_level = tier_config['pages']['headlines']['content_level']

    # 2. --- Fetch and Paginate Articles ---
    article_list = Article.objects.all().order_by('-published_at')
    paginator = Paginator(article_list, 15)  # Show 15 articles per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 3. --- Check for Stale Content ---
    is_stale = False
    if article_list.exists():
        latest_article = article_list.first()
        if latest_article.ingested_at < timezone.now() - timedelta(minutes=settings.TTL_MINUTES):
            is_stale = True

    context = {
        'page_obj': page_obj,
        'content_level': content_level,
        'is_stale': is_stale,
        'current_tier': current_tier, # Pass the tier for display if needed
    }
    return render(request, 'news.html', context)