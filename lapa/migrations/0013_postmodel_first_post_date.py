# Generated by Django 4.2.9 on 2024-02-24 09:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lapa', '0012_postmodel_subscribers'),
    ]

    operations = [
        migrations.AddField(
            model_name='postmodel',
            name='first_post_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='First post date'),
        ),
    ]