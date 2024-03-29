# Generated by Django 4.2.9 on 2024-02-01 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Text')),
                ('image', models.ImageField(upload_to='images/', verbose_name='Image')),
                ('sent', models.BooleanField(default=False, verbose_name='Sent')),
                ('pm', models.BooleanField(default=False, verbose_name='PM')),
                ('time', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12)], default=1, verbose_name='Time')),
                ('day_of_month', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30), (31, 31)], default=1, verbose_name='Day of month')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100, verbose_name='Username')),
                ('user_id', models.CharField(max_length=100, verbose_name='User ID')),
                ('webdriver', models.CharField(max_length=255, verbose_name='Webdriver')),
                ('selenium', models.CharField(max_length=100, verbose_name='Selenium')),
                ('timezone', models.CharField(default='UTC', max_length=100, verbose_name='Timezone')),
            ],
        ),
    ]
