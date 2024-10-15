URL = 'http://127.0.0.1:9000/accessories-electric-cars/{}.jpg'
from django.core.management.base import BaseCommand
from core.models import Product, Order, OrderProduct
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.crypto import get_random_string

PRODUCTS = [
    {   'id': 1,
        'name': 'Кронштейн подушки безопасности водителя',
        'part_number': '1456163-31-A',
        'price': '2697',
        'model_info': 'Tesla Model S рест. 2019',
        'year': '2019',
        'model': 'Model S',
        'article_number': '99458031',
        'brand': 'Tesla',
        'note': 'Кронштейн подушки безопасности водителя с электропроводкой, Tesla Model S Rest, X',
        'image': URL.format('1'),
    },
    {   'id': 2,
        'name': 'Накладка колесной арки задний левый',
        'part_number': '1035290-00-G',
        'price': '13485',
        'model_info': 'Tesla Model X 2019',
        'year': '2019',
        'model': 'Model X',
        'article_number': '99455421',
        'brand': 'Tesla',
        'note': 'Накладка колёсной арки, задней левой, оригинал, сломано одно крепление, Tesla Model X, XRest',
        'image': URL.format('2'),
    },
    {   'id': 3,
        'name': 'Подушка безопасности водителя',
        'part_number': '1023381-00-I',
        'price': '2325',
        'model_info': 'Tesla Model S 2016',
        'year': '2016',
        'model': 'Model S',
        'article_number': '9895148',
        'brand': 'Tesla',
        'note': 'Подушка безопасности водителя (под восстановление), Tesla Model S, SR, X',
        'image': URL.format('3'),
    },
    {   'id': 4,
        'name': 'Датчик уровня пневмоподвески',
        'part_number': '1027941-00-A',
        'price': '3441',
        'model_info': 'Tesla Model X 2019',
        'year': '2019',
        'model': 'Model X',
        'article_number': '994581',
        'brand': 'Tesla',
        'note': 'Датчик уровня пневмоподвески, передний левый, с кронштейном, Tesla Model X, S, SRest',
        'image': URL.format('4'),
    },
    {   'id': 5,
        'name': 'Усилитель заднего бампера',
        'part_number': '1041685-00-A',
        'price': '9765',
        'model_info': 'Tesla Model S рест. 2019',
        'year': '2019',
        'model': 'Model S',
        'article_number': '99459388',
        'brand': 'Tesla',
        'note': 'Усилитель заднего бампера, Tesla Model S, SRest, SRest 2',
        'image': URL.format('5'),
    },
    {   'id': 6,
        'name': 'Кронштейн крепления ручки',
        'part_number': '1008404-00-C',
        'price': '465',
        'model_info': 'Tesla Model S 2014',
        'year': '2014',
        'model': 'Model S',
        'article_number': '9878558',
        'brand': 'Tesla',
        'note': 'Кронштейн крепления ручки открытия двери внутренней задней правой Tesla Model S, Model S REST DOOR OPENER BRACKET - RIGHT REAR',
        'image': URL.format('6'),
    }
]

ORDERS = [
    {
        'order_id': 1,
        'order_number': 'eDUDmd1n7c',
        'order_date': '12.09.2024',
        'ship_date': '15.09.2024',
        'factory': 'Lathrop',
        'items': [
            {
                'product_id': 1,
                'quantity': 2,
            },
            {
                'product_id': 3,
                'quantity': 1,
            }
        ]
    },
    {
        'order_id': 2,
        'order_number': 'aN6zlwDbfh',
        'order_date': '24.09.2024',
        'ship_date': '26.09.2024',
        'factory': 'Fremont',
        'items': [
            {
                'product_id': 2,
                'quantity': 1,
            },
            {
                'product_id': 1,
                'quantity': 1,
            }
        ]
    },
    {
        'order_id': 3,
        'order_number': 'gYwHiiYtqS',
        'order_date': '25.09.2024',
        'ship_date': '28.09.2024',
        'factory': 'Nevada',
        'items': [
            {
                'product_id': 1,
                'quantity': 2,
            },
            {
                'product_id': 3,
                'quantity': 1,
            },
            {
                'product_id': 5,
                'quantity': 1,
            }
        ]
    },
    {
        'order_id': 4,
        'order_number': 'S0DOHugwQd',
        'order_date': '12.09.2024',
        'ship_date': '30.09.2024',
        'factory': 'New York',
        'items': [
            {
                'product_id': 2,
                'quantity': 1,
            },
            {
                'product_id': 4,
                'quantity': 2,
            },
            {
                'product_id': 5,
                'quantity': 1,
            }
        ]
    },
    {
        'order_id': 5,
        'order_number': 'XNK6A0bL82',
        'order_date': '20.09.2024',
        'ship_date': '25.09.2024',
        'factory': 'Shanghai',
        'items': [
            {
                'product_id': 1,
                'quantity': 2,
            },
            {
                'product_id': 3,
                'quantity': 1,
            },
            {
                'product_id': 6,
                'quantity': 2,
            }
        ]
    }
]

class Command(BaseCommand):
    help = 'Populates the database with initial data, including users, products, and orders'

    def handle(self, *args, **kwargs):
        # Создание 5 пользователей
        users = []
        for i in range(1, 6):
            username = f'user{i}'
            password = get_random_string(8)
            user, created = User.objects.get_or_create(
                username=username
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'User "{username}" created with password: {password}'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists.'))
            users.append(user)

        # Создание продуктов
        for product_data in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                part_number=product_data['part_number'],
                price=product_data['price'],
                model_info=product_data['model_info'],
                year=product_data['year'],
                model=product_data['model'],
                article_number=product_data['article_number'],
                brand=product_data['brand'],
                note=product_data.get('note', ''),
                image=product_data.get('image', None)
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Product "{product.name}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Product "{product.name}" already exists.'))

        # Создание заказов и привязка к пользователям
        for index, order_data in enumerate(ORDERS):
            order_date = datetime.strptime(order_data['order_date'], '%d.%m.%Y').date()
            ship_date = datetime.strptime(order_data['ship_date'], '%d.%m.%Y').date()

            creator = users[index % len(users)]  # Назначаем по одному из созданных пользователей на каждый заказ

            order, created = Order.objects.get_or_create(
                order_number=order_data['order_number'],  # Уникальный ключ
                defaults={
                    'order_date': order_date,
                    'ship_date': ship_date,
                    'factory': order_data['factory'],
                    'creator': creator
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Order {order.pk} created by {creator.username}.'))
            else:
                self.stdout.write(self.style.WARNING(f'Order {order.pk} already exists.'))

            # Создание продуктов для заказа
            for item_data in order_data['items']:
                product = Product.objects.get(pk=item_data['product_id'])
                order_product, created = OrderProduct.objects.get_or_create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity']
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Added {order_product.quantity}x {product.name} to Order {order.pk}.'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Product {product.name} already in Order {order.pk}.'
                    ))