from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Order, OrderProduct

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'part_number', 'price', 'model_info', 'year', 'model', 'article_number', 'brand', 'note', 'image']

class OrderProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderProduct
        fields = ['id', 'product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    order_products = OrderProductSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'order_date', 'ship_date', 'factory', 'total_cost', 'creator', 'moderator', 'status', 'order_products']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
