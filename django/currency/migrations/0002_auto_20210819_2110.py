# Generated by Django 3.2.6 on 2021-08-20 01:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0002_alter_team_emoji'),
        ('currency', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='current_message_id',
        ),
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initiating_party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='initiated_trades', to='team.team')),
                ('receiving_party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiving_trades', to='team.team')),
            ],
        ),
    ]
