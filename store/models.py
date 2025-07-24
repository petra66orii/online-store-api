import uuid
from django.db import models
from django.db.models import Sum
from django.conf import settings
from django_countries.fields import CountryField
from users.models import Customer

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    in_stock = models.BooleanField(default=True)


class Order(models.Model):
    """
    Order model to store order details
    and link to the user profile.

    Attributes:
        order_number (str): Unique identifier for the order.
        user_profile (ForeignKey): Link to the user profile.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        email (str): Email address of the user.
        phone_number (str): Phone number of the user.
        street_address1 (str): First line of the street address.
        street_address2 (str): Second line of the street address.
        country (str): Country of the user.
        town (str): Town of the user.
        county (str): County of the user.
        postcode (str): Postcode of the user.
        date (datetime): Date and time of the order.
        delivery_cost (Decimal): Cost of delivery.
        bag (str): JSON string of the items in the order.
        order_total (Decimal): Total cost of the items in the order.
        total_price (Decimal): Total price of the order including delivery.
        stripe_pid (str): Stripe payment ID.
        status (str): Status of the order (unfulfilled or fulfilled).
        """

    STATUS_CHOICES = [
        ('unfulfilled', 'Unfulfilled'),
        ('fulfilled', 'Fulfilled'),
    ]

    order_number = models.CharField(max_length=32, null=False, editable=False)
    user_profile = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
        )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    street_address1 = models.CharField(max_length=255)
    street_address2 = models.CharField(max_length=255, null=True, blank=True)
    country = CountryField(blank_label='Country *', null=False, blank=False)
    town = models.CharField(max_length=100)
    county = models.CharField(max_length=100, null=True, blank=True)
    postcode = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now_add=True)
    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
        )
    bag = models.TextField(null=False, blank=False, default='')
    order_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        default=0)
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        default=0)
    stripe_pid = models.CharField(
        max_length=254,
        null=False,
        blank=False,
        default=''
        )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unfulfilled',
    )

    def _generate_order_number(self):
        """
        Generate a random, unique order number using UUID
        """
        return uuid.uuid4().hex.upper()

    def update_total(self):
        """
        Update grand total each time an item is added,
        accounting for delivery costs.
        """
        self.order_total = self.items.aggregate(Sum('item_total'))[
            'item_total__sum'
            ] or 0
        if self.order_total < settings.FREE_DELIVERY_THRESHOLD:
            sdp = settings.STANDARD_DELIVERY_PERCENTAGE
            self.delivery_cost = self.order_total * sdp / 100
        else:
            self.delivery_cost = 0
        self.total_price = self.order_total + self.delivery_cost
        self.save()

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    """
    OrderItem model to store individual items in an order.

    Attributes:
        order (ForeignKey): Link to the order.
        product (ForeignKey): Link to the product.
        quantity (int): Quantity of the product.
        item_total (Decimal): Total cost of the item.
    """
    order = models.ForeignKey(
        Order,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='items'
        )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=False, blank=False, default=0)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """
        Override the original save method to set the item total
        and update the order total.
        """
        self.item_total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"
    