# Generated by Django 3.2.11 on 2022-01-26 15:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_location'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='county',
        ),
        migrations.RemoveField(
            model_name='location',
            name='town',
        ),
    ]
