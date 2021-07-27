# Generated by Django 3.2.4 on 2021-07-27 03:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0003_rename_current_message_transaction_current_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='from_wallet',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='from_wallet', to='currency.wallet'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='to_wallet',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='to_wallet', to='currency.wallet'),
        ),
    ]
