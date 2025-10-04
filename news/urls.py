from django.urls import path
from .views import home_view, article_detail_view

urlpatterns = [
    path('', home_view, name='home'),
    path('article/<int:article_id>/', article_detail_view, name='article_detail')
]