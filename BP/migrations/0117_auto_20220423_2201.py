# Generated by Django 3.2.11 on 2022-04-23 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0116_auto_20220423_2159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='litigation',
            name='county',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='litigation',
            name='state',
            field=models.CharField(default='', max_length=255, null=True),
        ),
    ]