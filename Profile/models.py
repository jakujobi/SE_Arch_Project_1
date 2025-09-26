from django.db import models
from django.contrib.auth.models import User

# Profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        # Update related User model if needed
        if hasattr(self, 'user'):
            self.user.save()
        super(Profile, self).save(*args, **kwargs)

# Subsciption
class Subscription(models.Model):
    user_id = models.ForeignKey('Profile.Profile', on_delete=models.CASCADE)
    TIER_CHOICES = [
    ("free", "Free"),
    ("standard", "Standard"),
    ("premium", "Premium"),
    ]
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default="free")
    start_date = models.DateField()
    end_date = models.DateField()

# PaymentHistory
class Payment(models.Model):
    user_id = models.ForeignKey('Profile.Profile', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=20, blank=True, null=True)