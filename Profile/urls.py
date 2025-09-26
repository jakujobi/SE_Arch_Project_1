from django.urls import path
from .views import profile, login_view, logout_view, register, edit_profile, payment

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('payment/', payment, name='payment'),
]