# Generated by Django 3.2.11 on 2022-04-15 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0101_clientproceeds'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientproceeds',
            name='check_date',
            field=models.CharField(default='', max_length=255, null=True),
        ),
    ]
