from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Order, OrderProduct, CustomUser
from collections import OrderedDict

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'part_number', 'price', 'model_info', 'year', 'model', 'article_number', 'brand', 'note', 'image']
    
    def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields 

class OrderProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderProduct
        fields = ['id', 'product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    order_products = OrderProductSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'creation_date', 'order_date', 'ship_date', 'factory', 'total_cost', 'creator', 'moderator', 'status', 'order_products']

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', None)
        super(OrderSerializer, self).__init__(*args, **kwargs)

        if exclude_fields:
            for field in exclude_fields:
                self.fields.pop(field, None)

class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']