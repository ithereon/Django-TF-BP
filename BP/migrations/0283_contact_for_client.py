# Generated by Django 3.2.11 on 2022-10-21 22:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0282_auto_20221018_2345'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='for_client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='BP.client'),
        ),
    ]
