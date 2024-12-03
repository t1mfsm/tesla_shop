import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.shortcuts import get_object_or_404
from django.utils import timezone
from core.permissions import IsAdmin, IsManager
from .models import Product, Order, OrderProduct, OrderStatus, CustomUser
from .serializers import ProductSerializer, OrderSerializer, OrderProductSerializer, UserSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from minio import Minio
from django.http import Http404, JsonResponse
from datetime import datetime
from rest_framework.response import *
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
import redis

session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator


# class UserSingleton:
#     _instance = None

#     @classmethod
#     def get_instance(cls):
#         if cls._instance is None:
#             try:
#                 cls._instance = User.objects.get(id=3)
#             except User.DoesNotExist:
#                 cls._instance = None
#         return cls._instance

#     @classmethod
#     def clear_instance(cls, user):
#         pass

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

        user = request.user
        car_order_id = None
        count_details = 0
        if user and user.is_authenticated:
            car_order = Order.objects.filter(creator=user, status='draft').first()
            if car_order:
                car_order_id = car_order.id
                count_details = car_order.get_total_detail_count()

        serializer = self.serializer_class(products, many=True)
        response_data = {
            'details': serializer.data,
            'car_order_id': car_order_id,
            'count_details': count_details
        }
        return Response(response_data, status=status.HTTP_200_OK)

    # POST: Добавление новой услуги
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def put(self, request, pk, format=None):
        product = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Удаление услуги и её изображения
    @method_permission_classes([IsManager])
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
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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
    @swagger_auto_schema(request_body=serializer_class)
    def add_to_draft(self, request, pk):
        user = request.user
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
        user = request.user
        if user.is_authenticated:
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            status = request.query_params.get('status')

            if user.is_authenticated:
                if user.is_staff:
                    orders = self.model_class.objects.all().exclude(status__in=['del'])
                else:
                    orders = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])
            else:
                return Response({"error": "Вы не авторизованы"}, status=401)
            
            if date_from:
                try:
                    date_from = datetime.strptime(date_from, '%Y-%m-%d')  # Пример: '2024-10-22'
                    orders = orders.filter(order_date__date__gte=date_from)
                except ValueError:
                    return Response({"error": "Invalid date_from format. Use 'YYYY-MM-DD'."}, status=400)

            if date_to:
                try:
                    date_to = datetime.strptime(date_to, '%Y-%m-%d')
                    orders = orders.filter(order_date__date__lte=date_to)
                except ValueError:
                    return Response({"error": "Invalid date_to format. Use 'YYYY-MM-DD'."}, status=400)

            if status:
                orders = orders.filter(status=status)

            serialized_orders = [
                {**self.serializer_class(order, exclude_fields=['order_products']).data,
                'creator': order.creator.email,
                'moderator': order.moderator.email if order.moderator else None}
                for order in orders
            ]

            return Response(serialized_orders)
        return Response(data={"error": "Вы не авторизованы."}, status=401)

class OrderDetail(APIView):
    model_class = Order
    serializer_class = OrderSerializer
    
    # GET: Получение информации о заявке
    def get(self, request, pk, format=None):
        order = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(order)
        data = serializer.data
        data['creator'] = order.creator.email
        if order.moderator:
            data['moderator'] = order.moderator.email
        for order_product in data.get('order_products', []):
            product_data = order_product.get('product', {})
            filtered_product_data = {
                'id': product_data.get('id'),
                'name': product_data.get('name'),
                'price': product_data.get('price'),
                'image': product_data.get('image')
            }
            order_product['product'] = filtered_product_data
            order_product.pop('id', None)
        return Response(data)

    # PUT: Изменение доп. полей заявки или изменение заявки модератором
    @swagger_auto_schema(request_body=serializer_class)

    def put(self, request, pk, format=None):
        # Получаем полный путь запроса
        full_path = request.path
        print('hello')
        if full_path.endswith('/form/'):
            return self.put_creator(request, pk)
        elif full_path.endswith('/complete/'):
            return self.put_moderator(request, pk)
        elif full_path.endswith('/edit/'):
            return self.put_edit(request, pk)

        return Response({"error": "Неверный путь"}, status=status.HTTP_400_BAD_REQUEST)

    # PUT для создателя: формирование заявки
    @method_permission_classes([AllowAny]) 
    def put_creator(self, request, pk):
        print('hello')
        dinner = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        if user.is_authenticated:
            if user == dinner.creator:

                # Проверка на обязательные поля
                

                # Установка статуса 'f' (сформирована) и даты формирования
                if 'status' in request.data and request.data['status'] == 'shipped':
                    dinner.formed_at = timezone.now()
                    updated_data = request.data.copy()

                    serializer = self.serializer_class(dinner, data=updated_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                return Response({"error": "Создатель может только формировать заявку."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)        
        return Response({"error": "Вы не авторизованы"}, status=401)    
    
    # PUT для модератора: завершение или отклонение заявки
    @method_permission_classes([IsManager])  # Разрешаем только модераторам
    def put_moderator(self, request, pk):
        dinner = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        
        if 'status' in request.data:
            status_value = request.data['status']

            # Модератор может завершить ('c') или отклонить ('r') заявку
            if status_value in ['delivered', 'cancelled']:
                if dinner.status != 'shipped':
                    return Response({"error": "Заявка должна быть сначала сформирована."}, status=status.HTTP_403_FORBIDDEN)

                # Установка даты завершения и расчёт стоимости для завершённых заявок
                if status_value == 'delivered':
                    real_time = timezone.now()
                    dinner.completed_at = real_time
                    total_cost = self.calculate_total_cost(dinner)
                    updated_data = request.data.copy()
                    updated_data['total_cost'] = total_cost

                elif status_value == 'cancelled':
                    dinner.completed_at = timezone.now()
                    updated_data = request.data.copy()

                serializer = self.serializer_class(dinner, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save(moderator=user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Модератор может только завершить или отклонить заявку."}, status=status.HTTP_400_BAD_REQUEST)

    def put_edit(self, request, pk):
        user = request.user
        if user.is_authenticated:
            dinner = get_object_or_404(self.model_class, pk=pk)

            if dinner.creator == user:
                # Обновление дополнительных полей
                serializer = self.serializer_class(dinner, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)

                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Вы не создатель заказа"}, status=403)
        return Response({"error": "Вы не авторизованы"}, status=401)

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
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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
    
class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    # def get_permissions(self):
    #     if self.action in ['create']:
    #         permission_classes = [AllowAny]
    #     elif self.action in ['list']:
    #         permission_classes = [IsAdmin | IsManager]
    #     else:
    #         permission_classes = [IsAdmin]
    #     return [permission() for permission in permission_classes]

    def get_permissions(self):
        # Удаляем ненужные проверки, чтобы любой пользователь мог обновить свой профиль
        if self.action == 'create' or self.action == 'profile':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request):
        # Проверка, существует ли уже пользователь с таким email
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)

        # Сериализация данных запроса
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # Создание пользователя с использованием сериализованных данных
            user = self.model_class.objects.create_user(
                email=serializer.data['email'],
                password=serializer.data['password'],
                is_superuser=serializer.data['is_superuser'],
                is_staff=serializer.data['is_staff']
            )

            # Подготовка данных о пользователе для ответа
            response_data = {
                'id': user.id,
                'email': user.email,
                'password': user.password,  # Включаем пароль (не рекомендуется на практике)
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
            }

            # Возвращение успешного ответа с данными о пользователе
            return Response({'status': 'Success', 'user': response_data})

        # В случае ошибок валидации сериализатора
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    # Обновление данных профиля пользователя
    @action(detail=False, methods=['put'], permission_classes=[AllowAny])
    def profile(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)

        # Получаем данные для обновления из запроса
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()  # Если данные валидны, сохраняем изменения
            return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @permission_classes([AllowAny])
# @authentication_classes([])
# @csrf_exempt
# @swagger_auto_schema(method='post', request_body=UserSerializer)
# @api_view(['POST'])
# def login_view(request):
#     email = request.data["email"]
#     password = request.data["password"]
#     user = authenticate(request, email=email, password=password)
#     print(user)
#     if user is not None:
#         login(request, user)
#         return HttpResponse("{'status': 'ok'}")
#     else:
#         return HttpResponse("{'status': 'error', 'error': 'login failed'}")

# def logout_view(request):
#     logout(request._request)
#     return Response({'status': 'Success'})

@authentication_classes([])
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    username = request.data["email"]
    password = request.data["password"]
    print(username)
    print(password)

    # Попытка аутентификации пользователя
    user = authenticate(request, email=username, password=password)

    if user is not None:
        # Создаем случайный ключ для сессии
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)  # Сохраняем сессию, если нужно

        # Сериализация данных пользователя
        user_data = UserSerializer(user)  # Сериализация объекта user
        response_data = user_data.data  # Извлекаем данные в словарь

        # Добавляем session_id в cookies
        response = JsonResponse({'status': 'ok', 'user': response_data})  # Отправляем данные пользователя
        response.set_cookie("session_id", random_key)

        return response
    else:
        # Если аутентификация не удалась
        return JsonResponse({'status': 'error', 'error': 'login failed'}, status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(method='post')
def logout_view(request):
    if request.user:
        session_id = request.COOKIES.get("session_id")
        if session_id:
            session_storage.delete(session_id)
            response = HttpResponse("{'status': 'ok'}")
            response.delete_cookie("session_id")
            return response
        else:
            return HttpResponse("{'status': 'error', 'error': 'no session found'}")
    return HttpResponse("{'error': 'Вы не авторизованы'}")