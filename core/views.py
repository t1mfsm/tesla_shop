from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .models import Product, Order, OrderStatus, OrderProduct
from urllib.parse import unquote
from django.utils.timezone import now
from django.contrib import messages
from django.db import connection
from django.db.models import F

def add_product_to_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    order, created = Order.objects.get_or_create(
        creator=user,
        status=OrderStatus.DRAFT,
        defaults={
            'order_date': now(),
            'factory': 'Tesla Factory'
        }
    )

    order_product, created = OrderProduct.objects.get_or_create(
        order=order, product=product,
        defaults={'quantity': 1}
    )

    if not created:
        order_product.quantity = F('quantity') + 1
        order_product.save()

    return redirect('main')


def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, creator=request.user)

    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE core_order
                SET status = %s
                WHERE id = %s
                """,
                ['cancelled', order_id]
            )

        messages.success(request, 'Ваш заказ был успешно удален.')
        return redirect('main')
    
    return redirect('car_order', order_id=order_id)

def main(request):
    user = request.user
    search_product = request.GET.get('search_product', '').lower() if request.GET.get('search_product') else None
    products = Product.objects.all()

    if search_product:
        products = products.filter(name__icontains=search_product)

    if user.is_authenticated:
        current_order = Order.objects.filter(creator=user, status='draft').first()
        has_order = current_order is not None and current_order.id is not None  # Check if the order exists
    else:
        current_order = None
        has_order = False

    return render(request, 'main.html', {
        'products': products,
        'search_product': search_product,
        'current_order': current_order,
        'has_order': has_order,
    })



def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    return render(request, 'product_detail.html', {'product': product})



def car_order(request, order_id):
    try:
        numeric_order_id = int(order_id.replace("order_", ""))
        order = Order.objects.get(id=numeric_order_id)

        if order.status == OrderStatus.CANCELLED:
            return render(request, 'order_not_found.html', {
                'message': 'Этот заказ был удалён.',
            })
        
        ordered_products = []
        total_sum = 0

        for order_item in order.order_products.all():
            product_with_quantity = order_item.product
            product_with_quantity.quantity = order_item.quantity
            ordered_products.append(product_with_quantity)
            total_sum += order_item.product.price * order_item.quantity

        return render(request, 'car_order.html', {
            'products': ordered_products, 
            'order_id': order.id,
            'order_date': order.order_date,
            'ship_date': order.ship_date,
            'factory': order.factory,
            'total_sum': total_sum,
            'current_order': order,
        })

    except Order.DoesNotExist:
        return render(request, 'order_not_found.html', {
            'message': 'Такого заказа не существует.',
        })