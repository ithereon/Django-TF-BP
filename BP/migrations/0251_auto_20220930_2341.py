# Generated by Django 3.2.11 on 2022-09-30 18:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BP', '0250_auto_20220930_2339'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccidentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Adjuster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Car',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('make', models.CharField(default='', max_length=255)),
                ('model', models.CharField(default='', max_length=255)),
                ('year', models.CharField(default='', max_length=255)),
                ('mileage', models.CharField(default='', max_length=255)),
                ('color', models.CharField(default='', max_length=255)),
                ('value', models.CharField(default='', max_length=255)),
                ('locationID', models.CharField(default='', max_length=255)),
                ('vehicle_note', models.TextField(blank=True, null=True)),
                ('propDamEst', models.CharField(default='', max_length=255)),
                ('propDamFinal', models.CharField(default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address1', models.TextField(blank=True, null=True)),
                ('address2', models.TextField(blank=True, null=True)),
                ('city', models.TextField(blank=True, null=True)),
                ('state', models.TextField(blank=True, null=True)),
                ('zip', models.TextField(blank=True, null=True)),
                ('phone_number', models.TextField(blank=True, null=True)),
                ('email', models.TextField(blank=True, null=True)),
                ('fax', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Injuries',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=255, null=True)),
                ('value', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.RenameField(
            model_name='caraccident',
            old_name='address',
            new_name='accident_note',
        ),
        migrations.RenameField(
            model_name='defendant',
            old_name='address1',
            new_name='defendant_note',
        ),
        migrations.RenameField(
            model_name='defendant',
            old_name='address2',
            new_name='liability_percent',
        ),
        migrations.RenameField(
            model_name='insurance',
            old_name='adjuster_address',
            new_name='account_number',
        ),
        migrations.RenameField(
            model_name='insurance',
            old_name='adjuster_email',
            new_name='claim_number',
        ),
        migrations.RenameField(
            model_name='insurance',
            old_name='adjuster_name',
            new_name='group_number',
        ),
        migrations.RenameField(
            model_name='insurance',
            old_name='adjuster_fax',
            new_name='policy_number',
        ),
        migrations.RenameField(
            model_name='otherparty',
            old_name='address1',
            new_name='party_dob',
        ),
        migrations.RenameField(
            model_name='otherparty',
            old_name='address2',
            new_name='party_first_name',
        ),
        migrations.RenameField(
            model_name='otherparty',
            old_name='city',
            new_name='party_last_name',
        ),
        migrations.RenameField(
            model_name='otherparty',
            old_name='birthday',
            new_name='party_middle_name',
        ),
        migrations.RenameField(
            model_name='otherparty',
            old_name='email',
            new_name='party_note',
        ),
        migrations.RenameField(
            model_name='witness',
            old_name='address1',
            new_name='witness_first_name',
        ),
        migrations.RenameField(
            model_name='witness',
            old_name='address2',
            new_name='witness_last_name',
        ),
        migrations.RenameField(
            model_name='witness',
            old_name='birthday',
            new_name='witness_middle_name',
        ),
        migrations.RenameField(
            model_name='witness',
            old_name='city',
            new_name='witness_note',
        ),
        migrations.RemoveField(
            model_name='caraccident',
            name='city',
        ),
        migrations.RemoveField(
            model_name='caraccident',
            name='state',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='address1',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='address2',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='city',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='email',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='loan_amount',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='state',
        ),
        migrations.RemoveField(
            model_name='caseloan',
            name='zip_code',
        ),
        migrations.RemoveField(
            model_name='defendant',
            name='city',
        ),
        migrations.RemoveField(
            model_name='defendant',
            name='email',
        ),
        migrations.RemoveField(
            model_name='defendant',
            name='note',
        ),
        migrations.RemoveField(
            model_name='defendant',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='defendant',
            name='post_code',
        ),
        migrations.RemoveField(
            model_name='defendant',
            name='state',
        ),
        migrations.RemoveField(
            model_name='injury',
            name='body_part',
        ),
        migrations.RemoveField(
            model_name='insurance',
            name='adjuster_phone',
        ),
        migrations.RemoveField(
            model_name='insurance',
            name='claim_no',
        ),
        migrations.RemoveField(
            model_name='insurance',
            name='for_defendant',
        ),
        migrations.RemoveField(
            model_name='insurance',
            name='policy_no',
        ),
        migrations.RemoveField(
            model_name='otherparty',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='otherparty',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='otherparty',
            name='note',
        ),
        migrations.RemoveField(
            model_name='otherparty',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='otherparty',
            name='post_code',
        ),
        migrations.RemoveField(
            model_name='otherparty',
            name='state',
        ),
        migrations.RemoveField(
            model_name='witness',
            name='email',
        ),
        migrations.RemoveField(
            model_name='witness',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='witness',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='witness',
            name='note',
        ),
        migrations.RemoveField(
            model_name='witness',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='witness',
            name='post_code',
        ),
        migrations.RemoveField(
            model_name='witness',
            name='state',
        ),
        migrations.AddField(
            model_name='caraccident',
            name='ambulance',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='caraccident',
            name='emergencyRoom',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='caraccident',
            name='lossOfConc',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='caraccident',
            name='reportTaken',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='defendant',
            name='defServedDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='defendant',
            name='liability_insurance_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='defendant_liability_insurance_id', to='BP.insurance'),
        ),
        migrations.AddField(
            model_name='defendant',
            name='middle_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='insurance',
            name='ERISAYN',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='insurance',
            name='UMLimit1',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='insurance',
            name='UMLimitAll',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='insurance',
            name='lien',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='insurance',
            name='lienFinal',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='insurance',
            name='midPayPipLimit',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='insurance',
            name='propDamLimit',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='otherparty',
            name='party_deposition_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='otherparty',
            name='party_served_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='witness',
            name='witness_birthday',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='witness',
            name='witness_deposition_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='witness',
            name='witness_served_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='defendant',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='defendant',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.CreateModel(
            name='InsuranceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=255)),
                ('policy_number', models.BooleanField(blank=True, default=False, null=True)),
                ('claim_number', models.BooleanField(blank=True, default=False, null=True)),
                ('UMLimit1', models.BooleanField(blank=True, default=False, null=True)),
                ('UMLimitAll', models.BooleanField(blank=True, default=False, null=True)),
                ('midPayPipLimit', models.BooleanField(blank=True, default=False, null=True)),
                ('propDamLimit', models.BooleanField(blank=True, default=False, null=True)),
                ('lien', models.BooleanField(blank=True, default=False, null=True)),
                ('lienFinal', models.BooleanField(blank=True, default=False, null=True)),
                ('medpayContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='insuranceType_medpayContact', to='BP.contact')),
                ('medpayPipLeinContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='insuranceType_medpayPipLeinContact', to='BP.contact')),
                ('pipContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='insuranceType_pipContact', to='BP.contact')),
                ('propDamContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='insuranceType_propDamContact', to='BP.contact')),
                ('unInsuredMotoristContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='insuranceType_unInsured', to='BP.contact')),
                ('underInsuredMotoristContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='insuranceType_underInsuredMotoristContact', to='BP.contact')),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(default='', max_length=255)),
                ('adjusters', models.ManyToManyField(blank=True, to='BP.Adjuster')),
            ],
        ),
        migrations.AddField(
            model_name='adjuster',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aduster_contact', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='caraccident',
            name='ClientCarId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='carAccident_clientcarid', to='BP.car'),
        ),
        migrations.AddField(
            model_name='caraccident',
            name='accident_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='BP.accidenttype'),
        ),
        migrations.AddField(
            model_name='caraccident',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='caraccident_contact', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='caraccident',
            name='defendantCarId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='carAccident_defendantcarid', to='BP.car'),
        ),
        migrations.AddField(
            model_name='caseloan',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='caseloans_contact', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='defendant',
            name='home_contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='defendant_home_contact', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='defendant',
            name='work_contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='defendant_work_contact', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='injury',
            name='injury',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='BP.injuries'),
        ),
        migrations.AddField(
            model_name='insurance',
            name='insurance_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='insurance_insurance_type', to='BP.insurancetype'),
        ),
        migrations.AddField(
            model_name='otherparty',
            name='party_contact_last',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='otherparty_last_contact', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='otherparty',
            name='party_home_contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='otherparty_home_contact', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='witness',
            name='witness_contact_home',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='witness_contact_home', to='BP.contact'),
        ),
        migrations.AddField(
            model_name='witness',
            name='witness_contact_last',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='witness_last_home', to='BP.contact'),
        ),
        migrations.AlterField(
            model_name='insurance',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Insurance_company', to='BP.company'),
        ),
    ]