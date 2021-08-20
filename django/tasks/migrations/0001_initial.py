# Generated by Django 3.2.6 on 2021-08-20 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Task",
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
                ("completed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "task_type",
                    models.CharField(
                        choices=[
                            ("MG", "Message"),
                            ("CT", "Change Team"),
                            ("CRO", "Create Role"),
                            ("CCA", "Create Category"),
                            ("CCH", "Create Channel"),
                            ("CDR", "Create Dropdown"),
                            ("CBT", "Create Buttons"),
                            ("TSR", "Create Transaction"),
                        ],
                        default="MG",
                        max_length=3,
                    ),
                ),
                ("payload", models.JSONField(default=dict)),
            ],
        ),
    ]
