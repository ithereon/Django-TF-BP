# Generated by Django 3.2.11 on 2022-03-04 17:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0042_alter_doc_check'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doc',
            name='document_type',
        ),
    ]
