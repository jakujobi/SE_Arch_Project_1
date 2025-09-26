"""
news/signals.py

Auto-create a UserProfile for new users and default them to 'free'.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

"""
from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):

    #Ensure every new user has a profile with tier='free'.

    if created:
        UserProfile.objects.create(user=instance, tier="free")
"""