# Generated by Django 3.2.4 on 2021-08-16 17:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("discord_roles", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="role",
            name="name",
        ),
    ]