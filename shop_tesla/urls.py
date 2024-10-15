from django.contrib import admin
from django.urls import include, path
from core import views
from rest_framework import routers

router = routers.DefaultRouter()
urlpatterns = [
    path('', include(router.urls)),
    path('products/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
    path('products/<int:pk>/draft/', views.ProductDetail.as_view(), name='product-add-to-draft'),
    path('products/<int:pk>/image/', views.ProductDetail.as_view(), name='product-image-upload'),
    path('orders/', views.OrderList.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetail.as_view(), name='order-detail'),
    path('orders/<int:order_id>/products/<int:product_id>/', views.OrderProductDetail.as_view(), name='order-product-detail'),
    path('users/<str:action>/', views.UserView.as_view(), name='user-action'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]