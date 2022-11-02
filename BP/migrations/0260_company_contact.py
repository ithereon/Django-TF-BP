# Generated by Django 3.2.11 on 2022-10-09 11:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0259_recentcases'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='company_contact', to='BP.contact'),
        ),
    ]
