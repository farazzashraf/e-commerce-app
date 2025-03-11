from django.db import models
from django.utils import timezone
import uuid

class User(models.Model):
    id = models.TextField(primary_key=True)  # Supabase stores user ID as TEXT
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if self.name else self.email


class PromoCode(models.Model):
    id = models.AutoField(primary_key=True)  # Integer primary key
    code = models.TextField(unique=True, blank=True, null=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)  # Example: 10.00 for 10% off
    valid = models.BooleanField(default=True)  # Indicates if the promo code is still valid
    expires_at = models.DateTimeField(null=True, blank=True)  # Expiration date of the promo code
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        """Returns True if the promo code is expired, else False."""
        return self.expires_at and self.expires_at < timezone.now()

    def __str__(self):
        return f"{self.code} - {'Expired' if self.is_expired() else 'Valid'}"


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, null=True, blank=True)  # Added missing field
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Added
    image_url = models.URLField(null=True, blank=True)
    image_url2 = models.URLField(null=True, blank=True)
    image_url3 = models.URLField(null=True, blank=True)
    image_url4 = models.URLField(null=True, blank=True)
    admin_id = models.TextField(null=True, blank=True)  # Added admin_id as TextField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Add this line
    is_deleted = models.BooleanField(default=False)  # New field for soft deletion
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', to_field="id", db_column="user_id")
    payment_method = models.TextField(null=True, blank=True)
    status = models.TextField(default='pending')
    address = models.JSONField(null=True, blank=True)  # Stores JSON data for the address
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        # Use user_id to access the related User instance.
        return f"Order {self.id} - {self.user_id.name if self.user_id.name else self.user_id.email}"



class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', db_column='order_id')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', db_column='product_id')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Item {self.id} - {self.name}"


class Cart(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart', to_field="id", db_column="user_id")
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.IntegerField(default=1)
    name = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'product_id')  # Ensures a user cannot add the same product multiple times

    def __str__(self):
        return f"Cart Item - {self.name} ({self.user_id.name if self.user_id.name else self.user_id.email})"

class AdminStore(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    firebase_uid = models.CharField(max_length=128, unique=True)
    company_logo =  models.URLField(null=True, blank=True)
    company_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    shop_address = models.TextField()
    pincode = models.CharField(max_length=10)
    is_approved = models.BooleanField(default=False)  # Approval system for admins

    def __str__(self):
        return self.company_name