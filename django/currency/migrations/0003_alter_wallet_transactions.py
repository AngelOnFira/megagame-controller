# Generated by Django 3.2.4 on 2021-07-08 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0002_auto_20210708_1844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallet',
            name='transactions',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='currency.transaction'),
        ),
    ]
