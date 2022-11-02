# Generated by Django 3.2.11 on 2022-02-21 23:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0021_auto_20220222_0200'),
    ]

    operations = [
        migrations.RenameField(
            model_name='litigation',
            old_name='address',
            new_name='county',
        ),
        migrations.AddField(
            model_name='litigation',
            name='federal_court',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='litigation',
            name='state',
            field=models.CharField(default='', max_length=255),
        ),
    ]
