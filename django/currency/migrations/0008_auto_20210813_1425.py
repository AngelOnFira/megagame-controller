# Generated by Django 3.2.4 on 2021-08-13 18:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0007_currency_emoji'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='from_wallet',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='credits', to='currency.wallet'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='to_wallet',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='debits', to='currency.wallet'),
        ),
    ]
