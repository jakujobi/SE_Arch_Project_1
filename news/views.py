from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseForbidden
from datetime import timedelta

from .models import Article


def home_view(request):
    """
    Displays the main headlines page with tier-aware content and pagination.
    """
    # 1. --- Determine User's Tier ---
    if request.user.is_authenticated:
        current_tier = request.user.profile.get_current_tier()
    else:
        current_tier = "anonymous"

    # Use settings.TIER_CONFIG to get this tier's config
    tier_config = settings.TIER_CONFIG.get(current_tier, settings.TIER_CONFIG['anonymous'])
    content_level = tier_config['pages']['headlines']['content_level']

    # 2. --- Fetch and Paginate Articles ---
    article_list = Article.objects.all().order_by('-published_at')
    paginator = Paginator(article_list, 15)  # 15 per page
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
        'current_tier': current_tier,  # pass tier to template
    }
    return render(request, 'news/news.html', context)


def article_detail_view(request, article_id):
    """
    Displays the details for a single article with tier-based restrictions.
    """
    article = get_object_or_404(Article, pk=article_id)

    # --- Determine User's Tier ---
    if request.user.is_authenticated:
        current_tier = request.user.profile.get_current_tier()
    else:
        current_tier = "anonymous"

    tier_config = settings.TIER_CONFIG.get(current_tier, settings.TIER_CONFIG['anonymous'])

    # --- Restrict anonymous users (no detail page allowed) ---
    if not tier_config['pages'].get('detail', False):
        return HttpResponseForbidden("Please sign in or upgrade your subscription to view this article.")

    context = {
        'article': article,
        'current_tier': current_tier,
        'content_level': tier_config['pages']['headlines']['content_level'],
    }
    return render(request, 'news/article_detail.html', context)
