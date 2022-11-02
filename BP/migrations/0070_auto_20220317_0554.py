# Generated by Django 3.2.11 on 2022-03-17 00:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0069_auto_20220317_0544'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attorney',
            name='user_type',
        ),
        migrations.AddField(
            model_name='attorney',
            name='user_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='BP.attorneyusertype'),
        ),
        migrations.RemoveField(
            model_name='attorneystaff',
            name='user_type',
        ),
        migrations.AddField(
            model_name='attorneystaff',
            name='user_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='BP.attorneyusertype'),
        ),
    ]
