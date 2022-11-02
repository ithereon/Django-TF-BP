# Generated by Django 3.2.11 on 2022-10-12 14:25

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0270_merge_20221011_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='doc',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='doc',
            name='ocr_status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('Done', 'Done'), ('Error', 'Error')], default='Pending', max_length=10),
        ),
        migrations.AddField(
            model_name='doc',
            name='ocr_tries',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='doc',
            name='upload',
            field=models.FileField(null=True, upload_to='documents/', validators=[django.core.validators.FileExtensionValidator(['pdf'])]),
        ),
        migrations.AlterField(
            model_name='doc_template',
            name='line_spacing',
            field=models.IntegerField(default=7, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10000)]),
        ),
        migrations.AlterField(
            model_name='doc_template',
            name='x_coord',
            field=models.IntegerField(default=13, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10000)]),
        ),
        migrations.AlterField(
            model_name='doc_template',
            name='y_coord',
            field=models.IntegerField(default=24, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10000)]),
        ),
        migrations.AlterField(
            model_name='hipaadoc',
            name='watermark',
            field=models.FileField(null=True, upload_to='documents/watermarks'),
        ),
        migrations.CreateModel(
            name='ocr_Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page_number', models.IntegerField(default=0)),
                ('text', models.TextField(blank=True, default='')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BP.doc')),
            ],
        ),
    ]
