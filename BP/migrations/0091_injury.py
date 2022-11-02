# Generated by Django 3.2.11 on 2022-04-08 15:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0039_auto_20220311_2216'),
        ('BP', '0090_panelcasechecklist_for_defendant'),
    ]

    operations = [
        migrations.CreateModel(
            name='Injury',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body_part', models.CharField(default='', max_length=255, null=True)),
                ('note', models.CharField(default='', max_length=255, null=True)),
                ('location', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='injury_location', to='accounts.location')),
                ('specialty', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='injury_specialty', to='accounts.specialty')),
            ],
        ),
    ]
