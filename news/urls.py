from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('article/<int:article_id>/', views.article_detail_view, name='article_detail'),
]
