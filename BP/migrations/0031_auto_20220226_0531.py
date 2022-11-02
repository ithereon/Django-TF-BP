# Generated by Django 3.2.11 on 2022-02-26 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0030_alter_statute_statute_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='defendant',
            name='claim_date',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='defendant',
            name='claim_rejected',
            field=models.CharField(default='False', max_length=255),
        ),
        migrations.AddField(
            model_name='defendant',
            name='expiry_date',
            field=models.CharField(default='', max_length=255, null=True),
        ),
    ]
