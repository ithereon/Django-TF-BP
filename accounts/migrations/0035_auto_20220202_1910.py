# Generated by Django 3.2.11 on 2022-02-02 14:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0034_providerstaff_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='providerstaff',
            name='password',
        ),
        migrations.RemoveField(
            model_name='providerstaff',
            name='username',
        ),
    ]