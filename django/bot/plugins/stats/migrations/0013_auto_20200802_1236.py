# Generated by Django 2.2.13 on 2020-08-02 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0012_auto_20190427_0202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gamesession',
            name='server',
            field=models.BigIntegerField(verbose_name='server'),
        ),
        migrations.AlterField(
            model_name='loggedmessage',
            name='discord_id',
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='loggedmessage',
            name='server',
            field=models.BigIntegerField(verbose_name='server'),
        ),
    ]
