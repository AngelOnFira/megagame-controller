# Generated by Django 3.2.6 on 2021-08-20 01:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("team", "0002_alter_team_emoji"),
        ("currency", "0003_auto_20210819_2114"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trade",
            name="initiating_party",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="initiated_trades",
                to="team.team",
            ),
        ),
        migrations.AlterField(
            model_name="trade",
            name="receiving_party",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receiving_trades",
                to="team.team",
            ),
        ),
    ]