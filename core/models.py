from django.db import models
from django.contrib.auth.models import User

# Product status choices
class ProductStatus(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    UNAVAILABLE = 'unavailable', 'Unavailable'

class Product(models.Model):
    name = models.CharField(max_length=255)
    part_number = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    model_info = models.CharField(max_length=255)
    year = models.PositiveIntegerField()
    model = models.CharField(max_length=255)
    article_number = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
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
    order_date = models.DateField()
    ship_date = models.DateField(blank=True, null=True)
    factory = models.CharField(max_length=255)
    creator = models.ForeignKey(User, related_name='created_orders', on_delete=models.CASCADE)
    moderator = models.ForeignKey(User, related_name='moderated_orders', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT
    )

    def __str__(self):
        return f"Order {self.id} - {self.status}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, related_name='order_products', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('order', 'product', 'user')

    def __str__(self):
        return f"Order {self.order.id} - Product {self.product.name} - User {self.user.username}"
