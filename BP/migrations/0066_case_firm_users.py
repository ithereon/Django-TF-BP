# Generated by Django 3.2.11 on 2022-03-16 20:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0065_auto_20220313_0622'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='firm_users',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='firmusers_cases', to='BP.attorneystaff'),
        ),
    ]