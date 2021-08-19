# Generated by Django 3.2.6 on 2021-08-19 20:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('currency', '0001_initial'),
        ('responses', '0001_initial'),
        ('discord_guilds', '0001_initial'),
        ('team', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=100)),
                ('guild', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='discord_guilds.guild')),
                ('responses', models.ManyToManyField(to='responses.Response')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='players', to='team.team')),
                ('wallet', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='currency.wallet')),
            ],
        ),
    ]
