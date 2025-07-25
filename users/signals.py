from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib import messages
from django.contrib.auth.models import User

from store.models import Order, Customer


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Creates a new UserProfile object for a newly created User.

    This signal handler is triggered upon saving a new User instance.
    If the `created` flag is True (indicating a new user), it creates
    a corresponding UserProfile object associated with the User.

    Args:
      sender: The User model class.
      instance: The newly created User object.
      created: A boolean flag indicating if a new user is created.
    """
    if created and not Customer.objects.filter(user=instance).exists():
        Customer.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Saves the user's profile whenever the User model is saved.

    Args:
        sender: The User model class.
        instance: The User object being saved.
        kwargs: Additional keyword arguments.
    """
    try:
        instance.customer.save()
    except Customer.DoesNotExist:
        pass



@receiver(post_save, sender=User)
def assign_guest_orders_to_new_user(sender, instance, created, **kwargs):
    """
    Assigns guest orders to a new user profile upon user creation.
    This signal handler is triggered when a new User instance is created.
    It links any guest orders (orders without a user profile) that
    match the user's email address to the newly created UserProfile.

    Args:
        sender: The User model class.
        instance: The newly created User object.
        created: A boolean flag indicating if a new user is created.
        kwargs: Additional keyword arguments.
    """
    if created:
        user = instance
        try:
            profile = user.customer
        except Customer.DoesNotExist:
            profile = Customer.objects.create(user=user)

        # Link orders with matching email that are still unassigned
        guest_orders = Order.objects.filter(
            user_profile__isnull=True,
            email=user.email
        )
        for order in guest_orders:
            order.user_profile = profile
            order.save()


@receiver(user_logged_in)
def assign_guest_orders_on_login(sender, request, user, **kwargs):
    """
    Assigns guest orders to a user profile upon user login.
    This signal handler is triggered when a user logs in.
    It links any guest orders (orders without a user profile)
    that match the user's email address to the user's UserProfile.
    Args:
        sender: The User model class.
        request: The HTTP request object.
        user: The User object being logged in.
        kwargs: Additional keyword arguments.
    """
    try:
        profile = user.customer
    except Customer.DoesNotExist:
        profile = Customer.objects.create(user=user)

    guest_orders = Order.objects.filter(
        user_profile__isnull=True,
        email=user.email
    )

    for order in guest_orders:
        order.user_profile = profile
        order.save()