# Generated by Django 3.2.4 on 2021-07-30 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('responses', '0001_initial'),
        ('player', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='responses',
            field=models.ManyToManyField(to='responses.Response'),
        ),
    ]
