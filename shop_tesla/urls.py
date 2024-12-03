from django.contrib import admin
from django.urls import include, path
from core import views
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('api/details/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('api/details/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
    path('api/details/<int:pk>/draft/', views.ProductDetail.as_view(), name='product-add-to-draft'),
    path('details/<int:pk>/image/', views.ProductDetail.as_view(), name='product-image-upload'),
    path('api/car_orders/', views.OrderList.as_view(), name='car_order-list'),
    path('api/car_orders/<int:pk>/', views.OrderDetail.as_view(), name='car_order-detail'),
    path('car_orders/<int:order_id>/details/<int:product_id>/', views.OrderProductDetail.as_view(), name='car_order-product-detail'),
    path('car_orders/<int:pk>/edit/', views.OrderDetail.as_view(), name='order-detail-edit'),
    path('api/car_orders/<int:pk>/form/', views.OrderDetail.as_view(), name='put_creator'),
    path('car_orders/<int:pk>/complete/', views.OrderDetail.as_view(), name='order-detail-complete'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/users/auth/', views.UserViewSet.as_view({'post': 'create'}), name='user-register'),
    path('api/login/',  views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),
    path('api/users/profile/', views.UserViewSet.as_view({'put': 'profile'}), name='profile')
]