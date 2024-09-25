#from django.contrib import admin
from django.urls import path

from .views import main, product_detail, car_order, add_product_to_order, delete_order

urlpatterns = [
    path('', main, name='main'),
    path('products/product_<int:product_id>', product_detail, name='product_detail'),
    path('car_order/<str:order_id>', car_order, name='car_order'),
    path('add_to_order/<int:product_id>/', add_product_to_order, name='add_to_order'),
    path('delete_order/<str:order_id>/', delete_order, name='delete_order'),
]