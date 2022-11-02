# Generated by Django 3.2.11 on 2022-05-26 22:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0180_case_created_by'),
        ('accounts', '0041_tftreatmentdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='tftreatmentdate',
            name='for_case_provider',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='case_provider_treatmentdate', to='BP.caseproviders'),
        ),
    ]