# Generated by Django 3.2.8 on 2021-11-21 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("currencies", "0003_auto_20211121_0701"),
    ]

    operations = [
        migrations.AddField(
            model_name="trade",
            name="first_iteration",
            field=models.BooleanField(default=True),
        ),
    ]
