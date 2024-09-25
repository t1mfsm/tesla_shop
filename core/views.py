from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .models import Product, Order, OrderStatus, OrderProduct
from unidecode import unidecode
from urllib.parse import unquote
from django.utils.timezone import now
from django.db import connection
from django.contrib import messages

def add_product_to_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    # Проверяем наличие черновика
    order, created = Order.objects.get_or_create(
        creator=user,
        status=OrderStatus.DRAFT,
        defaults={
            'order_date': now(),
            'factory': 'Tesla Factory'  # Можно изменить на нужное значение
        }
    )

    # Добавляем продукт в заявку или обновляем количество
    order_product, created = OrderProduct.objects.get_or_create(
        order=order, product=product, user=user,
        defaults={'quantity': 1}
    )
    
    if not created:
        order_product.quantity += 1
        order_product.save()

    return redirect('main')

def delete_order(request, order_id):
    # Находим заказ по ID и проверяем, что заказ принадлежит текущему пользователю
    order = get_object_or_404(Order, id=order_id, creator=request.user)

    if request.method == 'POST':
        # Удаляем заказ
        order.delete()
        messages.success(request, 'Ваш заказ был успешно удален.')
        return redirect('main')  # Возвращаем пользователя на главную страницу или другую

    return redirect('car_order', order_id=order_id)

def main(request):
    user = request.user
    search_product = request.GET.get('search_product', '').lower() if request.GET.get('search_product') else None
    products = Product.objects.all()

    if search_product:
        products = products.filter(name__icontains=search_product)

    current_order = Order.objects.filter(creator=user, status='draft').first()

    has_order = current_order is not None and current_order.id is not None  # Добавлена проверка наличия id

    return render(request, 'main.html', {
        'products': products,
        'search_product': search_product,
        'current_order': current_order,  # Передаем заказ в шаблон
        'has_order': has_order,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # Найти продукт по ID
    
    return render(request, 'product_detail.html', {'product': product})



def car_order(request, order_id):
    numeric_order_id = int(order_id.replace("order_", ""))
    order = get_object_or_404(Order, id=numeric_order_id, status=OrderStatus.DRAFT)

    ordered_products = []
    total_sum = 0

    for order_item in order.order_products.all():
        product_with_quantity = order_item.product
        product_with_quantity.quantity = order_item.quantity
        ordered_products.append(product_with_quantity)
        total_sum += order_item.product.price * order_item.quantity

    current_order = get_object_or_404(Order, id=order_id, creator=request.user)

    return render(request, 'car_order.html', {
        'products': ordered_products, 
        'order_id': order.id,
        'order_date': order.order_date,
        'ship_date': order.ship_date,
        'factory': order.factory,
        'total_sum': total_sum,  # Добавляем итоговую сумму
        'current_order': current_order,
    })
