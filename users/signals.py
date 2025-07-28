from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User

from store.models import Order, Customer


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, **kwargs):
    """
    Handles customer creation, saving, and assigning guest orders after a User is saved.
    """
    user = instance

    # Ensure customer exists
    customer, _ = Customer.objects.get_or_create(user=user)

    # If it's a new user, assign guest orders
    if created:
        guest_orders = Order.objects.filter(
            customer__isnull=True,
            email=user.email
        )
        for order in guest_orders:
            order.customer = customer
            order.save()


@receiver(user_logged_in)
def assign_guest_orders_on_login(sender, request, user, **kwargs):
    """
    Assigns guest orders to the user's customer profile on login.
    """
    customer, _ = Customer.objects.get_or_create(user=user)

    guest_orders = Order.objects.filter(
        customer__isnull=True,
        email=user.email
    )

    for order in guest_orders:
        order.customer = customer
        order.save()
