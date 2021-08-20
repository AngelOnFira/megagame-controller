# Generated by Django 3.2.6 on 2021-08-19 20:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("currency", "0001_initial"),
        ("discord_guilds", "0001_initial"),
        ("discord_roles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Team",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("emoji", models.CharField(blank=True, max_length=1, null=True)),
                (
                    "category",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="discord_roles.category",
                    ),
                ),
                (
                    "guild",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="discord_guilds.guild",
                    ),
                ),
                (
                    "role",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="discord_roles.role",
                    ),
                ),
                (
                    "wallet",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="currency.wallet",
                    ),
                ),
            ],
        ),
    ]
