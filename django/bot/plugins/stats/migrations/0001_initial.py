# Generated by Django 3.2.4 on 2021-07-07 13:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('channels', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Download',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('file', models.FileField(upload_to='downloads/%Y/%m/')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'download',
                'verbose_name_plural': 'downloads',
            },
        ),
        migrations.CreateModel(
            name='LoggedMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discord_id', models.BigIntegerField(unique=True)),
                ('server', models.BigIntegerField(verbose_name='server')),
                ('member_username', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('num_lines', models.PositiveSmallIntegerField(default=1)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('edited_timestamp', models.DateTimeField(blank=True, null=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='channels.channel')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='messages_authored', to='users.member')),
                ('mentions', models.ManyToManyField(blank=True, related_name='messages_mentioned_in', to='users.Member')),
            ],
            options={
                'verbose_name': 'message',
                'verbose_name_plural': 'messages',
                'ordering': ['-timestamp'],
            },
        ),
    ]
