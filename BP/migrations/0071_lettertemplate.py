# Generated by Django 3.2.11 on 2022-03-17 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0070_auto_20220317_0554'),
    ]

    operations = [
        migrations.CreateModel(
            name='LetterTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template', models.FileField(null=True, upload_to='images/')),
                ('category', models.CharField(default='', max_length=255, null=True)),
            ],
        ),
    ]
