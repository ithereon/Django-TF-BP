# Generated by Django 3.2.11 on 2022-03-04 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0041_alter_doc_upload'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doc',
            name='check',
            field=models.CharField(default='False', max_length=255, null=True),
        ),
    ]