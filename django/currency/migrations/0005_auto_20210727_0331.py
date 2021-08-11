# Generated by Django 3.2.4 on 2021-07-27 03:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0004_auto_20210727_0313'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='completed_date',
            new_name='modified_date',
        ),
        migrations.AlterField(
            model_name='transaction',
            name='current_message_id',
            field=models.IntegerField(default=0, unique=True),
        ),
    ]