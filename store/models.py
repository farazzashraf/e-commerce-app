from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, default='Uncategorized')  # New Category Field
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)  # Corrected
    admin_id = models.CharField(max_length=255)  # Store admin's unique ID

    def __str__(self):
        return self.name
 
# store/models.py
class Cart:
    def __init__(self, product_id, name, price, image_url, quantity):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.image_url = image_url
        self.quantity = quantity