# Generated by Django 3.2.11 on 2022-05-04 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0133_bankaccounts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incidentreport',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]