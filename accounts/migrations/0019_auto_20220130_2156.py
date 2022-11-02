# Generated by Django 3.2.11 on 2022-01-30 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_attorneylocation'),
    ]

    operations = [
        migrations.AddField(
            model_name='attorneylocation',
            name='email',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='attorneylocation',
            name='fax',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Fax'),
        ),
        migrations.AddField(
            model_name='attorneylocation',
            name='phone',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Phone'),
        ),
    ]