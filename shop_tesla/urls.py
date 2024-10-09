from django.contrib import admin
from django.urls import include, path
from core import views
from rest_framework import routers

router = routers.DefaultRouter()
urlpatterns = [
    path('', include(router.urls)),
    path('products/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
    path('products/<int:pk>/image/', views.ProductImageUpload.as_view(), name='product-image-upload'),
    path('orders/draft/add_product/', views.OrderDraftAddProduct.as_view(), name='order-draft-add-product'),
    path('orders/<int:pk>/', views.OrderDetail.as_view(), name='order-detail'),
    path('admin/', admin.site.urls),
]