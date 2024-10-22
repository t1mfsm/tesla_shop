from django.contrib import admin
from django.urls import include, path
from core import views
from rest_framework import routers

router = routers.DefaultRouter()
urlpatterns = [
    path('', include(router.urls)),
    path('details/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('details/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
    path('details/<int:pk>/draft/', views.ProductDetail.as_view(), name='product-add-to-draft'),
    path('details/<int:pk>/image/', views.ProductDetail.as_view(), name='product-image-upload'),
    path('car_orders/', views.OrderList.as_view(), name='car_order-list'),
    path('car_orders/<int:pk>/', views.OrderDetail.as_view(), name='car_order-detail'),
    path('car_orders/<int:order_id>/details/<int:product_id>/', views.OrderProductDetail.as_view(), name='car_order-product-detail'),
    path('users/<str:action>/', views.UserView.as_view(), name='user-action'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]