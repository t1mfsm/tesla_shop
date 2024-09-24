URL = 'http://127.0.0.1:9000/accessories-electric-cars/{}.jpg'
from django.shortcuts import render
from django.http import Http404

PRODUCTS = [
    {   'id': 1,
        'name': 'Кронштейн подушки безопасности водителя',
        'part_number': '1456163-31-A',
        'price': '2 697 ₽',
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
        'price': '13 485 ₽',
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
        'price': '2 325 ₽',
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
        'price': '3 441 ₽',
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
        'price': '9 765 ₽',
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
        'price': '465 ₽',
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
    }
]


def main(request):
    search_product = request.GET.get('search_product', '').lower() if request.GET.get('search_product') else None
    if search_product:
        products = [product for product in PRODUCTS if search_product in product['name'].lower()]
    else:
        products = PRODUCTS

    return render(request, 'main.html', {'products': products, 'search_product': search_product})


def product_detail(request, product_name):  # Убедитесь, что здесь используется 'product_name'
    product = None
    for product_item in PRODUCTS:
        if product_item['name'].lower() == product_name.lower():
            product = product_item
            break

    if not product:
        raise Http404("Продукт не найден")

    return render(request, 'product_detail.html', {'product': product})



def car_order(request, order_id):
    if order_id.startswith("order_"):
        numeric_order_id = int(order_id.replace("order_", ""))
    else:
        raise Http404("Неверный формат идентификатора заказа")
    
    order = next((order for order in ORDERS if order['order_id'] == numeric_order_id), None)
    
    if not order:
        raise Http404("Заказ не найден")
    
    ordered_products = []

    for order_item in order['items']:
        for product in PRODUCTS:
            if product['id'] == order_item['product_id']:
                product_with_quantity = product.copy()
                product_with_quantity['quantity'] = order_item['quantity']
                ordered_products.append(product_with_quantity)

    return render(request, 'car_order.html', {
        'products': ordered_products, 
        'order_id': numeric_order_id,
        'order_date': order['order_date'],
        'ship_date': order['ship_date'],
        'factory': order['factory']
    })
