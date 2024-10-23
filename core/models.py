from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, BaseUserManager

class NewUserManager(UserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        verbose_name=('groups')
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text=('Specific permissions for this user.'),
        verbose_name=('user permissions')
    )

    USERNAME_FIELD = 'email'

    objects = NewUserManager()

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
    image = models.CharField(max_length=255, blank=True)
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
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    order_date = models.DateTimeField()
    ship_date = models.DateTimeField(blank=True, null=True)
    factory = models.CharField(max_length=255)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    creator = models.ForeignKey(CustomUser, related_name='created_orders', on_delete=models.CASCADE)
    moderator = models.ForeignKey(CustomUser, related_name='moderated_orders', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(
        max_length=15,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT
    )

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = get_random_string(10)
        super().save(*args, **kwargs)

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
    