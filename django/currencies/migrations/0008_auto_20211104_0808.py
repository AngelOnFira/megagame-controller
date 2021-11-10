# Generated by Django 3.2.8 on 2021-11-04 12:08

import django_fsm

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("currencies", "0007_auto_20211103_1740"),
    ]

    operations = [
        migrations.AddField(
            model_name="currency",
            name="currency_type",
            field=models.CharField(
                choices=[
                    ("ADM", "Admin"),
                    ("COM", "Common"),
                    ("RAR", "Rare"),
                    ("LOG", "Logistics"),
                    ("HID", "Hidden"),
                    ("SPE", "Special"),
                ],
                default="HID",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="trade",
            name="state",
            field=django_fsm.FSMField(default="initiating_party_view", max_length=50),
        ),
    ]