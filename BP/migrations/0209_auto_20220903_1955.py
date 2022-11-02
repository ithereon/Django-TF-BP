# Generated by Django 3.2.11 on 2022-09-03 14:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0208_alter_client_ssn'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clickrecord',
            name='clickIDName',
        ),
        migrations.RemoveField(
            model_name='clickrecord',
            name='for_page',
        ),
        migrations.CreateModel(
            name='Click',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('click_id', models.IntegerField(blank=True, default=0, null=True)),
                ('clickIDName', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('for_page', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='click_record_page', to='BP.page')),
            ],
        ),
        migrations.AlterField(
            model_name='clickrecord',
            name='click',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='click_record', to='BP.click'),
        ),
    ]
