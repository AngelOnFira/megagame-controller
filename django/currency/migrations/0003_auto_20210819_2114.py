# Generated by Django 3.2.6 on 2021-08-20 01:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0002_auto_20210819_2110'),
    ]

    operations = [
        migrations.AddField(
            model_name='trade',
            name='currency_lookup',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='trade',
            name='team_lookup',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
