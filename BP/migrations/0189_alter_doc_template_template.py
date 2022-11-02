# Generated by Django 3.2.11 on 2022-07-25 20:04

import BP.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0188_doc_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doc_template',
            name='template',
            field=models.FileField(default='doc_templates/alignment_test_template.pdf', null=True, upload_to=BP.models.update_filename, validators=[django.core.validators.FileExtensionValidator(['pdf'])]),
        ),
    ]
