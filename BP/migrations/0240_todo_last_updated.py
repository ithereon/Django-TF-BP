# Generated by Django 3.2.11 on 2022-09-25 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0239_alter_workunit_checklist'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
