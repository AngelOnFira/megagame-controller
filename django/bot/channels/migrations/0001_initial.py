# Generated by Django 3.2.4 on 2021-07-09 01:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discord_id', models.BigIntegerField(unique=True)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('allow_nsfw', models.BooleanField(default=False)),
            ],
        ),
    ]
