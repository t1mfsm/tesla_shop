# Ваша миграция core/0002_order_order_number.py

from django.db import migrations, models
import django.utils.crypto

def generate_order_numbers(apps, schema_editor):
    Order = apps.get_model('core', 'Order')
    for order in Order.objects.all():
        order.order_number = django.utils.crypto.get_random_string(10)
        order.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.RunPython(generate_order_numbers),  # Заполняем поле order_number
    ]
