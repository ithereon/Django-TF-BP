# Generated by Django 3.2.11 on 2022-09-07 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0213_auto_20220908_0049'),
    ]

    operations = [
        migrations.AddField(
            model_name='click',
            name='clickIDName',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
    ]
