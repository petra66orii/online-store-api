import uuid
from django.db import models
from django_countries.fields import CountryField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
class Customer(models.Model):
    """
    User Profile model to store additional information about the user.
    This model extends the default User model to include fields
    such as phone number, address, and location.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    street_address1 = models.CharField(max_length=255)
    street_address2 = models.CharField(max_length=255, null=True, blank=True)
    country = CountryField(blank_label='Country', null=True, blank=True)
    county = models.CharField(max_length=100, null=True, blank=True)
    town = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username
    
    @receiver(post_save, sender=User)
    def create_or_update_user_profile(sender, instance, created, **kwargs):
        """
        Create or update the user profile
        """
        if created:
            Customer.objects.create(user=instance)
        # Existing users: just save the profile
        instance.customer.save()


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).total_seconds() > 86400  # 24 hours
