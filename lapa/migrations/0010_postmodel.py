# Generated by Django 4.2.9 on 2024-02-22 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lapa', '0009_profile_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100, verbose_name='Username')),
                ('date_joined', models.DateTimeField(blank=True, null=True, verbose_name='Date joined')),
            ],
        ),
    ]
