# Generated by Django 3.2.8 on 2021-11-23 13:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("currencies", "0004_trade_first_iteration"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="payment",
            name="completion_amount",
        ),
        migrations.AddField(
            model_name="payment",
            name="fundraising_amount",
            field=models.BooleanField(default=False),
        ),
    ]
