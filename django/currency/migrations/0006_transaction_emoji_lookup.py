# Generated by Django 3.2.4 on 2021-07-30 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0005_auto_20210727_0331'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='emoji_lookup',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]