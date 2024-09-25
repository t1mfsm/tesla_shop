from django.contrib import admin
from .models import Product, Order, OrderProduct

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderProduct)
