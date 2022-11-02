# Generated by Django 3.2.11 on 2022-05-23 13:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0172_rename_case_types_casestage_case_statuses'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='case_stage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='case_stages', to='BP.casestage'),
        ),
    ]
