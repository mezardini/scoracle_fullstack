# Generated by Django 4.0.4 on 2023-12-09 07:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_prediction_league'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prediction',
            name='league',
        ),
    ]
