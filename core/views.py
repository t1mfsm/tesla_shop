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
    }
]

ORDERS = [
    {
        'order_id': 1,
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

    return render(request, 'main.html', {'products': PRODUCTS})


def product_detail(request, product_id):

    product = None
    for product_item in PRODUCTS:
        if product_item['id'] == product_id:
            product = product_item

    if not product:
        raise Http404

    return render(request, 'product_detail.html', {'product': product})


def basket(request, order_id):
    order = next((order for order in ORDERS if order['order_id'] == order_id), None)
    
    if not order:
        raise Http404("Заказ не найден")
    
    ordered_products = []

    for order_item in order['items']:
        for product in PRODUCTS:
            if product['id'] == order_item['product_id']:
                # Копируем данные товара и добавляем количество
                product_with_quantity = product.copy()
                product_with_quantity['quantity'] = order_item['quantity']
                ordered_products.append(product_with_quantity)

    return render(request, 'basket.html', {'products': ordered_products, 'order_id': order_id})

def product_search(request):
    query = request.GET.get('query', '').lower()
    if query:
        products = [product for product in PRODUCTS if query in product['name'].lower()]
    else:
        products = []
    return render(request, 'search_results.html', {'products': products, 'query': query})
