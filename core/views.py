from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Product, Order, OrderProduct
from .serializers import ProductSerializer, OrderSerializer
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from minio import Minio

class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                # Здесь вместо id=11 будет логика получения первого пользователя
                cls._instance = User.objects.first()
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('accessories-electric-cars', image_name, file_object, file_object.size)
        return f"http://localhost:9000/accessories-electric-cars/{image_name}"
    except Exception as e:
        return {"error": str(e)}

def add_pic(new_product, pic):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{new_product.id}.jpg"

    if not pic:
        return {"error": "Нет файла для изображения."}

    result = process_file_upload(pic, client, img_obj_name)
    
    if 'error' in result:
        return {"error": result['error']}

    return result 

class ProductListCreate(APIView):
    model_class = Product
    serializer_class = ProductSerializer

    # GET: Список услуг
    def get(self, request, format=None):
        name = request.query_params.get('name')

        products = self.model_class.objects.filter(status='available')
        if name:
            products = products.filter(name__icontains=name)

        user = UserSingleton.get_instance()
        draft_order_id = None
        if user:
            draft_order = Order.objects.filter(creator=user, status='draft').first()
            if draft_order:
                draft_order_id = draft_order.id

        serializer = self.serializer_class(products, many=True)
        response_data = {
            'products': serializer.data,
            'draft_order_id': draft_order_id
        }
        return Response(response_data, status=status.HTTP_200_OK)

    # POST: Добавление новой услуги
    def post(self, request, format=None):
        pic = request.FILES.get("image")
        data = request.data.copy()
        data.pop('image', None) 
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            product = serializer.save()
            if pic:
                pic_url = add_pic(product, pic)
                if 'error' in pic_url:
                    return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)
                product.image = pic_url
                product.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetail(APIView):
    # GET: Получение одной услуги по id
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    # PUT: Обновление услуги
    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Удаление услуги и её изображения
    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.image = ''  # Удаляем изображение
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductImageUpload(APIView):
    # POST: Добавление изображения для услуги
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        image = request.data.get('image')
        if image:
            product.image = image  # Обновляем изображение
            product.save()
            return Response({'status': 'image updated'}, status=status.HTTP_200_OK)
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

# Order APIView
class OrderDraftAddProduct(APIView):
    # POST: Добавление продукта в заявку-черновик
    def post(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        # Получаем или создаем черновик для пользователя
        draft_order, created = Order.objects.get_or_create(
            creator=user,
            status='draft',
            defaults={'order_date': timezone.now()}
        )
        
        # Получаем продукт и добавляем его в заявку
        product = get_object_or_404(Product, pk=product_id)
        order_product, _ = OrderProduct.objects.get_or_create(
            order=draft_order,
            product=product,
            defaults={'quantity': quantity}
        )

        # Обновляем количество, если продукт уже есть в заявке
        if not created:
            order_product.quantity += quantity
            order_product.save()

        return Response({'status': 'product added to draft', 'order_id': draft_order.id})

class OrderDetail(APIView):
    # GET: Получение информации о заявке
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    # PUT: Обновление заявки
    def put(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Удаление заявки
    def delete(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
