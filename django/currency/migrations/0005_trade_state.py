# Generated by Django 3.2.6 on 2021-08-20 01:31

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0004_auto_20210819_2119'),
    ]

    operations = [
        migrations.AddField(
            model_name='trade',
            name='state',
            field=django_fsm.FSMField(default='new', max_length=50),
        ),
    ]
