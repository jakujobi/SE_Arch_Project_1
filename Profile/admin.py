from django.contrib import admin
from .models import Profile, Subscription, Payment

# Register your models here.
admin.site.register(Profile)
admin.site.register(Subscription)
admin.site.register(Payment)