# Generated by Django 3.2.11 on 2022-06-04 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0053_alter_tfaccounting_payment_received_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='otherlocations',
            name='name',
        ),
        migrations.AddField(
            model_name='otherlocations',
            name='address',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='Address1'),
        ),
        migrations.AddField(
            model_name='otherlocations',
            name='address2',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='Address2'),
        ),
        migrations.AddField(
            model_name='otherlocations',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='City'),
        ),
        migrations.AddField(
            model_name='otherlocations',
            name='post_code',
            field=models.CharField(blank=True, default='', max_length=8, null=True, verbose_name='Post Code'),
        ),
        migrations.AddField(
            model_name='otherlocations',
            name='state',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='State'),
        ),
    ]
