# Generated by Django 3.2.11 on 2022-04-20 23:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0114_alter_notes_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notes',
            options={'ordering': ('-created_at',)},
        ),
    ]
