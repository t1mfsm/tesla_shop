from django.db import models
from django.contrib.auth.models import User

# Product status choices
class ProductStatus(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    UNAVAILABLE = 'unavailable', 'Unavailable'

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    part_number = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    model_info = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    model = models.CharField(max_length=50)
    article_number = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    note = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255)
    status = models.CharField(
        max_length=15,
        choices=ProductStatus.choices,
        default=ProductStatus.AVAILABLE
    )

    def __str__(self):
        return self.name

class OrderStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING = 'pending', 'Pending'
    SHIPPED = 'shipped', 'Shipped'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    order_date = models.DateField()
    ship_date = models.DateField(blank=True, null=True)
    factory = models.CharField(max_length=255)
    creator = models.ForeignKey(User, related_name='created_orders', on_delete=models.CASCADE)
    moderator = models.ForeignKey(User, related_name='moderated_orders', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(
        max_length=15,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT
    )

    def __str__(self):
        return f"Order {self.id} - {self.status}"

class OrderProduct(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, related_name='order_products', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"Order {self.order.id} - Product {self.product.name}"
