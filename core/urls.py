#from django.contrib import admin
from django.urls import path

from .views import main, product_detail, basket

urlpatterns = [
    path('', main, name='main'),
    path('products/<int:product_id>', product_detail, name='product_detail'),
    path('basket/<int:order_id>', basket, name='basket'),
]