# Generated by Django 3.2.11 on 2022-05-19 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0167_requestupdate_requested_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestupdate',
            name='isRequested',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
