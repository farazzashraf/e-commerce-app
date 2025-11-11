from django.db import models
from django.utils import timezone
import uuid
from django.utils.text import slugify

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
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Create a unique slug by combining category and subcategory names
            self.slug = slugify(f"{self.category.name}-{self.name}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        verbose_name_plural = "Subcategories"
        ordering = ['category__name', 'name']


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Added
    sizes = models.CharField(max_length=100, blank=True)
    fit = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(null=True, blank=True)
    image_url2 = models.URLField(null=True, blank=True)
    image_url3 = models.URLField(null=True, blank=True)
    image_url4 = models.URLField(null=True, blank=True)
    admin_id = models.ForeignKey(
        AdminStore,  # Ensure AdminStore model exists
        on_delete=models.CASCADE,
        related_name="products",
        db_column="admin_id"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Add this line
    is_deleted = models.BooleanField(default=False)  # New field for soft deletion
    stock = models.IntegerField(default=1)
    
    def __str__(self):
        return f"Product {self.id} - {self.name} ({self.admin_id.company_name if self.admin_id else 'No Admin'})"
    
    def delete(self, *args, **kwargs):
        """Soft delete instead of actual deletion."""
        self.is_deleted = True
        self.save()
    class Meta:
        ordering = ["-created_at"]  # Show latest products first

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=10, blank=True, null=True)
    fit = models.CharField(max_length=100, blank=True)  # e.g. "Slim fit", "Regular fit"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, null=True)  # Main variant image
    # Field to store additional image URLs (as a JSON array)
    additional_image_urls = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.color} ({self.size or 'Standard'})"
    
class Order(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', to_field="id", db_column="user_id")
    # New field: Reference to the seller (admin store)
    admin = models.ForeignKey(
        AdminStore, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    payment_method = models.TextField(null=True, blank=True)
    status = models.TextField(default='pending')
    address = models.JSONField(null=True, blank=True)  # Stores JSON data for the address
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        # Display admin's company name for clarity
        admin_name = self.admin.company_name if self.admin else "Unknown Store"
        user_name = self.user_id.name if self.user_id.name else self.user_id.email
        return f"Order {self.id} - {user_name} (Store: {admin_name})"


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', db_column='order_id')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', db_column='product_id')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.TextField(null=True, blank=True)
    # Optional: add the seller for this particular order item.
    admin = models.ForeignKey(
        AdminStore, 
        on_delete=models.CASCADE, 
        related_name='order_items', 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"Item {self.id} - {self.name} (Store: {self.admin.company_name if self.admin else 'Unknown'})"


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
