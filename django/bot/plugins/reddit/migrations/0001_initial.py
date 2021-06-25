# Generated by Django 3.2.4 on 2021-06-25 16:30

import bot.plugins.reddit.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RedditCommand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command', bot.plugins.reddit.models.LowerCaseCharField(max_length=100, unique=True, verbose_name='command')),
                ('subreddit', bot.plugins.reddit.models.LowerCaseCharField(max_length=50, verbose_name='subreddit')),
                ('times_used', models.PositiveIntegerField(default=0)),
                ('nsfw', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['subreddit'],
                'unique_together': {('command', 'subreddit')},
            },
        ),
    ]
