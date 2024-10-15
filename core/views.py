from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Product, Order, OrderProduct, OrderStatus
from .serializers import ProductSerializer, OrderSerializer, OrderProductSerializer, UserSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from minio import Minio
from django.http import Http404
from rest_framework.response import *

class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = User.objects.get(id=3)
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

    @classmethod
    def clear_instance(cls, user):
        pass

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
        data = request.data.copy()
        data.pop('image', None) 
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetail(APIView):
    model_class = Product
    serializer_class = ProductSerializer

    # GET: Получение одной услуги по id
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    # PUT: Обновление услуги
    def put(self, request, pk, format=None):
        product = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(product, data=request.data, partial=True)
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

    def post(self, request, pk, format=None):
        if request.path.endswith('/image/'):
            return self.update_image(request, pk)
        elif request.path.endswith('/draft/'):
            return self.add_to_draft(request, pk)
        raise Http404
    
    # POST: Изменение фото услуги
    def update_image(self, request, pk):
        product = get_object_or_404(self.model_class, pk=pk)
        pic = request.FILES.get("image")

        if not pic:
            return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

        if product.image:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            old_img_name = product.photo.split('/')[-1]
            try:
                client.remove_object('accessories-electric-cars', old_img_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении старого изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pic_url = add_pic(product, pic)
        if 'error' in pic_url:
            return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)

        product.image = pic_url
        product.save()

        return Response({"message": "Изображение успешно обновлено.", "photo_url": pic_url}, status=status.HTTP_200_OK)

    # POST: Добавленеи услуги в заявку-черновик
    def add_to_draft(self, request, pk):
        user = UserSingleton.get_instance()
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        product = get_object_or_404(self.model_class, pk=pk)
        draft_order = Order.objects.filter(creator=user, status=OrderStatus.DRAFT).first()

        if not draft_order:
            draft_order = Order.objects.create(
                order_date=timezone.now(),
                creator=user,
                factory='Tesla Factory',
                status=OrderStatus.DRAFT
            )
            draft_order.save()

        if OrderProduct.objects.filter(order=draft_order, product=product).exists():
            return Response(data={"error": "Деталь уже добавлена в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        OrderProduct.objects.create(order=draft_order, product=product, quantity=1)

        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderList(APIView):
    model_class = Order
    serializer_class = OrderSerializer

    # GET: Список заявок
    def get(self, request, format=None):
        user = UserSingleton.get_instance()

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        orders = self.model_class.objects.filter(creator=user).exclude(status__in=[OrderStatus.DRAFT, OrderStatus.CANCELLED])

        if date_from:
            orders = orders.filter(order_date__gte=date_from)
        if date_to:
            orders = orders.filter(order_date__lte=date_to)

        if status:
            orders = orders.filter(status=status)

        serialized_orders = [
            {**self.serializer_class(order).data, 'creator': order.creator.username, 'moderator': order.moderator.username if order.moderator else None}
            for order in orders
        ]

        return Response(serialized_orders)
    
    # PUT: Создание заявки
    def put(self, request, format=None):
        user = UserSingleton.get_instance()
        required_fields = ['order_number']
        for field in required_fields:
            if field not in request.data or request.data[field] is None:
                return Response({field: 'Это поле обязательно для заполнения.'}, status=status.HTTP_400_BAD_REQUEST)

        order_id = request.data.get('id')
        if order_id:
            order = get_object_or_404(self.model_class, pk=order_id)
            serializer = self.serializer_class(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            order = serializer.save(creator=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetail(APIView):
    model_class = Order
    serializer_class = OrderSerializer
    
    # GET: Получение информации о заявке
    def get(self, request, pk, format=None):
        order = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(order)
        data = serializer.data
        data['creator'] = order.creator.username
        if order.moderator:
            data['moderator'] = order.moderator.username
        return Response(data)

    # PUT: Изменение доп. полей заявки или изменение заявки модератором
    def put(self, request, pk, format=None):
        order = get_object_or_404(self.model_class, pk=pk)
        user = UserSingleton.get_instance()

        if 'status' in request.data:
            status_value = request.data['status']

            if status_value not in ['shipped', 'received']:
                return Response({"error": "Неверный статус."}, status=status.HTTP_400_BAD_REQUEST)

            total_cost = self.calculate_total_cost(order)
            updated_data = request.data.copy()
            updated_data['total_cost'] = total_cost

            order.ship_date = timezone.now().date()

            serializer = self.serializer_class(order, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)

        serializer = self.serializer_class(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(moderator=user)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def calculate_total_cost(self, order):
        total_cost = 0
        order_products = order.order_products.all()

        for order_product in order_products:
            product_price = order_product.product.price
            quantity = order_product.quantity
            total_cost += product_price * quantity

        return total_cost

    # DELETE: Удаление заявки
    def delete(self, request, pk, format=None):
        order = get_object_or_404(self.model_class, pk=pk)
        order.status = 'cancelled'
        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class OrderProductDetail(APIView):
    model_class = OrderProduct
    serializer_class = OrderProductSerializer

    # PUT: Изменение доп. поля
    def put(self, request, order_id, product_id, format=None):
        order = get_object_or_404(Order, pk=order_id)
        order_product = get_object_or_404(self.model_class, order=order, product__id=product_id)

        serializer = self.serializer_class(order_product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Удаление детали из заявки
    def delete(self, request, order_id, product_id, format=None):
        order = get_object_or_404(Order, pk=order_id)
        order_product = get_object_or_404(self.model_class, order=order, product__id=product_id)

        order_product.delete()
        return Response({"message": "Товар успешно удалён из заказа"}, status=status.HTTP_204_NO_CONTENT)
    
class UserView(APIView):
    
    # POST: регистрация, аутентификация и деавторизация пользователя
    def post(self, request, action, format=None):
        if action == 'register':
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                user = User(
                    username=validated_data['username'],
                    email=validated_data['email']
                )
                user.set_password(request.data.get('password'))
                user.save()
                return Response({
                    'message': 'Регистрация прошла успешно'
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'authenticate':
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                user_data = UserSerializer(user).data
                return Response({
                    'message': 'Аутентификация успешна',
                    'user': user_data
                }, status=200)
            
            return Response({'error': 'Неправильное имя пользователя или пароль'}, status=400)

        elif action == 'logout':
            return Response({'message': 'Вы вышли из системы'}, status=200)

        return Response({'error': 'Некорректное действие'}, status=400)

    # PUT: личный кабинет пользователя
    def put(self, request, action, format=None):
        if action == 'profile':
            user = UserSingleton.get_instance()
            if user is None:
                return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
            
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)