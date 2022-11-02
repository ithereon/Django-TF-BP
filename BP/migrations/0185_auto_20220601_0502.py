# Generated by Django 3.2.11 on 2022-06-01 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0184_alter_bpaccounting_for_case_provider'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bpaccounting',
            name='final',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='bpaccounting',
            name='hi_paid',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='bpaccounting',
            name='hi_reduction',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='bpaccounting',
            name='mp_paid',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='bpaccounting',
            name='original',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='bpaccounting',
            name='reduction',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
    ]
