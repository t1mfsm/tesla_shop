#from django.contrib import admin
from django.urls import path

from .views import main, product_detail, car_order

urlpatterns = [
    path('', main, name='main'),
    path('products/<str:product_name>', product_detail, name='product_detail'),
    path('car_order/<str:order_id>', car_order, name='car_order'),
]