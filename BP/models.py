from math import degrees
from os import execv
from re import X
import rlcompleter
from unicodedata import category
from django.db import models
from django.contrib.auth.models import User
from accounts.models import Location, Specialty, Provider, ProviderStaff
from django.db.models import Q

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# jairo

import os
from django.core.validators import FileExtensionValidator
from django.core.validators import MaxValueValidator, MinValueValidator 
from django.db.models.signals import pre_save, post_save
from .utils import create_stamped_file

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

class Firm(models.Model):
    user = models.OneToOneField(User, related_name='bp_userprofile', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=False, null=False, default='')
    last_name = models.CharField(max_length=100, blank=False, null=False, default='')
    email = models.CharField(max_length=200, default='NA', null=False)
    account_type = models.CharField(max_length=100, blank=False, null=False, default='')
    mailing_email = models.CharField(max_length=255, null=True, blank=True, default='')
    mailing_password = models.CharField(max_length=255, null=True, blank=True, default='')
    office_name = models.CharField(max_length=255, blank=False, null=False, default='')

class AttorneyUserType(models.Model):
    name = models.CharField(null=False, default='', max_length=255)
    order = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        ordering = ('order', )
    def __str__(self):
        return self.name



class Factors(models.Model):
    name = models.CharField(max_length=255, null=True)
    def __str__(self):
        return self.name


class Contact(models.Model):
    address1 = models.TextField(null=True, blank=True)
    address2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    phone_number = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    fax = models.TextField(null=True, blank=True)
    


class CaseType(models.Model):
    name = models.CharField(max_length=255, null=True)
    # pages = models.ManyToManyField(Page, related_name="casetypes_pages")
    user_types = models.ManyToManyField(AttorneyUserType, related_name="casetypes_usertypes")

    factors = models.ManyToManyField(Factors, related_name='case_type_factors', blank=True)
    def __str__(self):
        return self.name

class Page(models.Model):
    name = models.CharField(max_length=255, null=True, default='')
    html_template_name = models.CharField(max_length=255, null=True, default='')
    case_types = models.ManyToManyField(CaseType, related_name='page_case_types', blank=True)
    page_url = models.CharField(max_length=255, null=True, default='', blank=True)
    order = models.IntegerField(default=0, null=True, blank=True)
    page_icon = models.FileField(upload_to="images/", null=True, blank=True, validators=[FileExtensionValidator(['svg', 'jpg', 'jpeg', 'png'])])

    class Meta:
        ordering = ('order', )
    def __str__(self):
        return self.name

class Rank(models.Model):
    name = models.CharField(max_length=255, null=True)
    value = models.IntegerField(default=0, null=True, blank=True)
    def __str__(self):
        return self.name

class Attorney(models.Model):
    attorneyprofile = models.ForeignKey(Firm, related_name='bp_attorney_userprofile', on_delete=models.CASCADE)
    
    marketer_code = models.CharField(max_length=255, null=True)
    user_type =  models.ForeignKey(AttorneyUserType, null=True, on_delete=models.SET_NULL)

    shakespeare_status = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return self.attorneyprofile.office_name

class FactorScale(models.Model):
    firm = models.ForeignKey(Attorney, related_name='factorscale_firm', null=True, blank=True, on_delete=models.CASCADE)
    factor = models.ForeignKey(Factors, related_name='factorscale_factor', null=True, blank=True, on_delete=models.CASCADE)
    min = models.IntegerField(default=0, null=True, blank=True)
    max = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return str(self.factor.name + " ( " + str(self.min) + ", " + str(self.max) + " )")

class FirmRank(models.Model):
    firm = models.ForeignKey(Attorney, related_name='firmrank_firm', null=True, blank=True, on_delete=models.CASCADE)
    factor_scale = models.ForeignKey(FactorScale, related_name='firmrank_factor_scale', null=True, blank=True, on_delete=models.SET_NULL)
    rank = models.ForeignKey(Rank, null=True, related_name='firmrank_rank', blank=True, on_delete=models.SET_NULL)
    case_type = models.ForeignKey(CaseType, null=True, blank=True, related_name='firmrank_case_type', on_delete=models.CASCADE)




class ClientStatus(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, default='')

    def __str__(self):
        return self.name

class Status(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, default='')

    def __str__(self):
        return self.name
    

class Stage(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, default='')
    order = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        ordering = ('order', )
    def __str__(self):
        return self.name

class CaseStage(models.Model):
    name = models.CharField(max_length=255, null=True)
    case_statuses = models.ManyToManyField(ClientStatus, related_name="casestage_types", blank=True)
    order = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        ordering = ('order', )

    def __str__(self):
        return self.name

class AttorneyStaff(models.Model):
    created_by = models.ForeignKey(Attorney, on_delete=models.CASCADE)
    user = models.OneToOneField(User, related_name='bp_attorneystaff_userprofile',null=True, on_delete=models.CASCADE)
    account_type = models.CharField(null=False, default='AttorneyStaff', max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    team = models.ManyToManyField('self', related_name='user_team')
    phone_extension = models.CharField(null=False, default='', max_length=255)
    isIntake = models.BooleanField(default=False, null=True, blank=True)
    # user_type = models.CharField(null=False, default='case manager', max_length=255)
    user_type = models.ManyToManyField(AttorneyUserType)
    accounting_permission = models.CharField(null=True, default='False', max_length=255, blank=True)
    accounting_admin_permission = models.CharField(null=True, default='False', max_length=255, blank=True)

    def __str__(self):
        return self.user.username

class AttorneyLocation(models.Model):
    added_by = models.ForeignKey(Attorney, related_name='bp_location_attorney', on_delete=models.CASCADE)
    address = models.CharField(verbose_name="Address1",max_length=100, null=True, blank=True, default='')
    address2 = models.CharField(verbose_name="Address2",max_length=100, null=True, blank=True, default='')
    city = models.CharField(verbose_name="City",max_length=100, null=True, blank=True, default='')
    state = models.CharField(verbose_name="State",max_length=100, null=True, blank=True, default='')
    post_code = models.CharField(verbose_name="Post Code",max_length=8, null=True, blank=True, default='')
    country = models.CharField(verbose_name="Country",max_length=100, null=True, blank=True, default='')
    phone = models.CharField(verbose_name="Phone",max_length=100, null=True, blank=True)
    fax = models.CharField(verbose_name="Fax",max_length=100, null=True, blank=True)
    email = models.CharField(verbose_name="Email",max_length=100, null=True, blank=True)

class EmergencyContact(models.Model):
    first_name = models.CharField(max_length=100, null=False, default='', blank=True)
    last_name = models.CharField(max_length=100, null=False, default='', blank=True)
    relationship = models.CharField(max_length=100, null=False, default='', blank=True)
    discussCase = models.BooleanField(null=True, default=False, blank=True)
    contact = models.ForeignKey(Contact, related_name='emergency_contact', on_delete=models.CASCADE, null=True, blank=True)


class Client(models.Model):
    created_by = models.ForeignKey(Attorney, related_name='bp_clients_attorney', on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=100, null=True, default='', blank=True)
    middle_name = models.CharField(max_length=100, null=True, default='', blank=True)
    last_name = models.CharField(max_length=100, null=True, default='', blank=True)
    title = models.CharField(max_length=100, null=True, default='', blank=True)
    phone = models.CharField(max_length=100, null=True, default='', blank=True)
    email = models.CharField(max_length=100, null=True, default='', blank=True)
    contact_1 = models.ForeignKey(Contact, related_name='client_contact1', on_delete=models.PROTECT, null=True, blank=True)
    contact_2 = models.ForeignKey(Contact, related_name='client_contact2', on_delete=models.PROTECT, null=True, blank=True)
    contact_3 = models.ForeignKey(Contact, related_name='client_contact3', on_delete=models.PROTECT, null=True, blank=True)
    primary_email = models.ForeignKey(Contact, related_name='client_primary_email', on_delete=models.PROTECT, null=True, blank=True)
    primary_phone = models.ForeignKey(Contact, related_name='client_primary_phone', on_delete=models.PROTECT, null=True, blank=True)
    mailing_contact = models.ForeignKey(Contact, related_name='client_mailing_contact', on_delete=models.PROTECT, null=True, blank=True)
    emergency_contact = models.ForeignKey(EmergencyContact, related_name='client_emergency_contact', on_delete=models.PROTECT, null=True, blank=True)
    birthday = models.CharField(max_length=100, null=True, default='', blank=True)
    gender =  models.CharField(max_length=100, null=True, default='', blank=True)
    age =  models.IntegerField(null=True, default=0, blank=True)
    profile_pic = models.ImageField(upload_to='images/', null=True, blank=True)
    status = models.OneToOneField(ClientStatus, related_name='client_statuses', null=True, on_delete=models.SET_NULL, blank=True)
    client_user = models.ForeignKey(User, related_name='client_user', null=True, on_delete=models.CASCADE)
    ssn = models.IntegerField(null=True, blank=True, default=0)
    driver_license_number = models.CharField(max_length=255, null=True, blank=True)
    driver_license_state = models.CharField(max_length=255, null=True, blank=True)
    

    def __str__(self):
        return self.first_name

class CheckList(models.Model):
    page = models.ForeignKey(Page, related_name='checklist_page', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, default='')
   

    def __str__(self):
        return self.name

class WorkUnit(models.Model):
    wu_name = models.CharField(max_length=100, blank=False, null=False, default='')
    table = models.CharField(max_length=100, blank=False, null=False, default='')
    field = models.CharField(max_length=100, blank=False, null=False, default='')
    field_description = models.TextField(null=True, blank=True)
    filled = models.BooleanField(default=False, null=True, blank=True)
    any = models.BooleanField(default=False, null=True, blank=True)
    all = models.BooleanField(default=False, null=True, blank=True)
    empty = models.BooleanField(default=False, null=True, blank=True)
    valued = models.BooleanField(default=False, null=True, blank=True)
    more = models.CharField(max_length=100, null=False, default='', blank=True)
    less = models.CharField(max_length=100, null=False, default='', blank=True)
    max = models.CharField(max_length=100, null=False, default='', blank=True)
    min = models.CharField(max_length=100, null=False, default='', blank=True)
    min = models.CharField(max_length=100, null=False, default='', blank=True)
    related_name = models.CharField(max_length=100, null=False, default='', blank=True)
    blocked_status = models.ManyToManyField(Status, related_name="blocked_status_wu", blank=True)
    checklist = models.ForeignKey(CheckList, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.wu_name)

class Act(models.Model):
    act_name = models.CharField(max_length=100, blank=False, null=False, default='')
    work_units = models.ManyToManyField(WorkUnit, blank=True)

    def __str__(self):
        return str(self.act_name)

class ActCaseStatus(models.Model):
    firm = models.ForeignKey(Attorney, related_name='act_case_status_firm', on_delete=models.CASCADE, null=True, blank=True)
    act = models.ForeignKey(Act, related_name='act_case_status_act', on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(Status, related_name='act_case_status_status', on_delete=models.CASCADE, null=True, blank=True)
    

class ActCaseStage(models.Model):
    act = models.ForeignKey(Act, related_name='act_case_stage_act', on_delete=models.CASCADE, null=True, blank=True)
    stage = models.ForeignKey(Stage, related_name='act_case_stage_stage', on_delete=models.CASCADE, null=True, blank=True)

class Case(models.Model):
    created_by = models.ForeignKey(User, related_name='created_case_user', on_delete=models.SET_NULL, null=True)
    for_client = models.ForeignKey(Client, related_name='client_cases', on_delete=models.CASCADE, null=True)
    incident_date =  models.CharField(max_length=100, blank=False, null=False, default='')
    # case_type = models.CharField(max_length=100, blank=False, null=False, default='')
    case_type = models.ForeignKey(CaseType, on_delete=models.SET_NULL, null=True)
    case_category = models.CharField(max_length=100, null=True, blank=True)
    # case_status = models.CharField(max_length=100, blank=False, null=True, default='New Lead')
    date_closed = models.CharField(max_length=100, null=True, default='', blank=True)
    court_jurisdiction = models.CharField(max_length=100, null=True, default='', blank=True)
    open = models.CharField(max_length=100, null=True, default='True')
    case_status = models.ForeignKey(ClientStatus, related_name='case_statuses', null=True, on_delete=models.SET_NULL, blank=True)
    case_stage = models.ForeignKey(CaseStage, related_name='case_stages', null=True, on_delete=models.SET_NULL, blank=True)
    firm_users = models.ManyToManyField(AttorneyStaff, related_name='firmusers_cases', blank=True)

    original = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    hi_paid = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    hi_reduction = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    mp_paid = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    reduction = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    final = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)

    auto_case_status = models.ManyToManyField(Status, related_name='auto_case_statuses', blank=True)
    auto_case_stage = models.ManyToManyField(Stage, related_name='auto_case_stages', blank=True)

    case_rank = models.ForeignKey(Rank, related_name='case_case_rank', null=True, blank=True, on_delete=models.SET_NULL)

    property_damage_value = models.CharField(max_length=255, null=True, blank=True, default='')

    def __str__(self):
        return self.incident_date

class RequestUpdate(models.Model):
    for_case = models.ForeignKey(Case, related_name='case_request_update', on_delete=models.CASCADE)
    status_changed_on = models.CharField(max_length=100, null=True, default='True')
    changed_by = models.ForeignKey(User, related_name='status_change_user', on_delete=models.SET_NULL, null=True)
    recent_status = models.TextField(null=True)
    isRequested = models.BooleanField(default=False, null=True, blank=True)
    requested_at = models.CharField(max_length=100, null=True, default='True')
    request_count = models.IntegerField(default=0, null=True, blank=True)



class CaseProviders(models.Model):
    
    for_case = models.ForeignKey(Case, related_name='for_case_caseproviders', on_delete=models.CASCADE, null=True)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='bp_provider_location')
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name='bp_provider_specialty')
    visits = models.CharField(max_length=100, blank=True, null=True, default='__')
    first_date = models.CharField(max_length=100, blank=True, null=True, default='_/_/_')
    second_date = models.CharField(max_length=100, blank=True, null=True, default='_/_/_')

    check_number = models.CharField(max_length=100, blank=False,  default='')
    # amount = models.DecimalField(decimal_places=2, max_digits=10,  default=0)
    # ins_paid = models.DecimalField(decimal_places=2, max_digits=10,  default=0)
    # write_off = models.DecimalField(decimal_places=2, max_digits=10,  default=0)
    # reduction = models.DecimalField(decimal_places=2, max_digits=10,  default=0)
    # final_amount = models.DecimalField(decimal_places=2, max_digits=10,  default=0)
    
    


    tf_case_status = models.ForeignKey('accounts.TFCaseStatus', related_name='tf_case_statuses', null=True, on_delete=models.SET_NULL)
    is_open = models.BooleanField(default=True, null=True, blank=True)
    
    treatment_location = models.ForeignKey(Contact, on_delete = models.PROTECT,related_name='Treatment_Location', null= True, blank = True)
    billing_request = models.ForeignKey(Contact, on_delete = models.PROTECT, related_name='Billing_Request', null= True, blank = True)
    records_request = models.ForeignKey(Contact, on_delete = models.PROTECT, related_name='Records_Request', null= True, blank = True)
    billing_request_paid = models.ForeignKey(Contact, on_delete = models.PROTECT, related_name='Billing_Pequest_Paid', null= True, blank = True)
    records_request_paid = models.ForeignKey(Contact, on_delete = models.PROTECT,related_name='Records_Request_Paid', null= True, blank = True)
    lien_holder = models.ForeignKey(Contact, on_delete = models.PROTECT,related_name='Lien_Holder', null= True, blank = True)

    def __str__(self):
        try:
            return str(self.provider.providerprofile.office_name)
        except:
            return "Case Provider Obj"
    

class BPAccounting(models.Model):
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    for_case_provider = models.OneToOneField(CaseProviders, related_name='bp_case_provider_accounting', on_delete=models.CASCADE, null=True)
    original = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    hi_paid = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    hi_reduction = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    mp_paid = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    reduction = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    final = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# jairo

class Doc(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True) 
    # upload = models.FileField(upload_to='documents/', null=True)
    upload = models.FileField(upload_to='documents/', null=True, blank=True, validators=[FileExtensionValidator(['pdf'])])
    file_name = models.CharField(max_length=255, null=True, blank=True, default='')
    page_name = models.CharField(max_length=255, null=True, blank=True, default='')
    document_no = models.CharField(max_length=255, null=True, blank=True, default='')
    check = models.CharField(max_length=255, null=True, blank=True, default='False')
    ocr_StatusChoices = [ ('Pending', 'Pending'), ('Processing', 'Processing'), ('Done', 'Done'), ('Error', 'Error') ]
    ocr_tries = models.PositiveSmallIntegerField(default=0)
    ocr_status = models.CharField(max_length=10, choices=ocr_StatusChoices, default='Pending')
    created = models.DateTimeField(auto_now_add=True)

    provider_documents = models.ForeignKey(CaseProviders, related_name='provider_docs', null=True, blank=True, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.pk)


class ocr_Page(models.Model):
    page_number = models.IntegerField(default=0)
    text = models.TextField(blank=True, default='')
    document = models.ForeignKey(Doc, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.document.file_name} - page: {self.page_number}"

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

class HIPAADoc(models.Model):
    for_firm = models.OneToOneField(Attorney, related_name='HIPAA_for_atttorney', on_delete=models.CASCADE)
    x_value = models.CharField(max_length=255, null=True, default='')
    y_value = models.CharField(max_length=255, null=True, default='')
    template = models.ForeignKey(Doc, related_name="HIPAA_doc", on_delete=models.CASCADE, null=True)
    watermark = models.FileField(upload_to='documents/watermarks', null=True)




class ClientLocation(models.Model):
    added_by = models.ForeignKey(Client, related_name='bp_location_Client', on_delete=models.CASCADE)
    address = models.CharField(verbose_name="Address1",max_length=100, null=True, blank=True, default='')
    address2 = models.CharField(verbose_name="Address2",max_length=100, null=True, blank=True, default='')
    city = models.CharField(verbose_name="City",max_length=100, null=True, blank=True, default='')
    state = models.CharField(verbose_name="State",max_length=100, null=True, blank=True, default='')
    post_code = models.CharField(verbose_name="Post Code",max_length=8, null=True, blank=True, default='')
    
    

class TreatmentDates(models.Model):
    for_provider = models.ForeignKey(CaseProviders, related_name="bp_treatment_notes", on_delete=models.CASCADE, null=True)
    description = models.TextField(null=True, default='')
    date = models.CharField(max_length=100, blank=False, null=True, default='')

    document = models.OneToOneField(Doc, related_name='treatmentnote_doc', null=True, on_delete=models.SET_NULL)



class State(models.Model):
    name = models.CharField(max_length=255, null=True, default='')
    StateAbr = models.CharField(max_length=255, null=True, blank=True, default='')
    def __str__(self):
        return self.name

class County(models.Model):
    in_state = models.ForeignKey(State, null=True, related_name='county_states', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, default='')
    population = models.CharField(max_length=255, null=True, default='', blank=True)
    population_date = models.CharField(max_length=255, null=True, default='', blank=True)
    def __str__(self):
        return self.name


class Notes(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    for_client = models.ForeignKey(Client,  related_name='client_notes', on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    description = models.TextField(null=True)
    category = models.ForeignKey(Page, related_name="notes_category", null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ('-created_at',)
    def __str__(self):
        return self.category.name
    
    

class InsuranceType(models.Model):
    name = models.CharField(max_length=255, null=False, default='')
    # unInsuredMotoristContact = models.BooleanField(default=False, null=True, blank=True)
    # underInsuredMotoristContact = models.BooleanField(default=False, null=True, blank=True)
    # medpayContact = models.BooleanField(default=False, null=True, blank=True)
    # pipContact = models.BooleanField(default=False, null=True, blank=True)
    # medpayPipLeinContact = models.BooleanField(default=False, null=True, blank=True)
    # propDamContact = models.BooleanField(default=False, null=True, blank=True)
    policy_number = models.BooleanField(default=False, null=True, blank=True)
    claim_number = models.BooleanField(default=False, null=True, blank=True)
    UMLimit1 = models.BooleanField(default=False, null=True, blank=True)
    UMLimitAll = models.BooleanField(default=False, null=True, blank=True)
    midPayPipLimit = models.BooleanField(default=False, null=True, blank=True)
    propDamLimit = models.BooleanField(default=False, null=True, blank=True)
    lien = models.BooleanField(default=False, null=True, blank=True)
    lienFinal = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return str(self.name)

class Adjuster(models.Model):
    first_name = models.CharField(max_length=255, null=False, default='')
    middle_name = models.CharField(max_length=255, null=False, default='')
    last_name = models.CharField(max_length=255, null=False, default='')
    contact = models.ForeignKey(Contact, related_name='aduster_contact', null=True, blank=True, on_delete=models.CASCADE)
    def __str__(self):
        try:
            return str(self.first_name + " " + self.last_name)
        except:
            return "Adjuster Obj"
class Company(models.Model):
    company_name = models.CharField(max_length=255, null=False, default='')
    contact = models.ForeignKey(Contact, related_name="company_contact", null=True, blank=True, on_delete=models.CASCADE)
    adjusters = models.ManyToManyField(Adjuster, blank=True)

    def __str__(self):
        return str(self.company_name)

class Insurance(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    # for_defendant = models.ForeignKey(Defendant, related_name="defendant_insurances", on_delete=models.CASCADE, null=True)
    # company = models.CharField(max_length=255, null=False, default='')
    # policy_no = models.CharField(max_length=255, null=False, default='')
    # claim_no = models.CharField(max_length=255, null=False, default='')
    # adjuster_name = models.CharField(max_length=255, null=False, default='')
    # adjuster_address = models.CharField(max_length=255, null=False, default='')
    # adjuster_phone = models.CharField(max_length=255, null=False, default='')
    # adjuster_fax = models.CharField(max_length=255, null=False, default='')
    # adjuster_email = models.CharField(max_length=255, null=False, default='')
    company = models.ForeignKey(Company, related_name='Insurance_company', null=True, blank=True, on_delete=models.SET_NULL)
    insurance_type = models.ForeignKey(InsuranceType, related_name='insurance_insurance_type', null=True, blank=True, on_delete=models.SET_NULL)
    unInsuredMotoristContact = models.ForeignKey(Contact, related_name='insuranceType_unInsured', null=True, blank=True, on_delete=models.CASCADE)
    underInsuredMotoristContact = models.ForeignKey(Contact, related_name='insuranceType_underInsuredMotoristContact', null=True, blank=True, on_delete=models.CASCADE)
    medpayContact = models.ForeignKey(Contact, related_name='insuranceType_medpayContact', null=True, blank=True, on_delete=models.CASCADE)
    pipContact = models.ForeignKey(Contact, related_name='insuranceType_pipContact', null=True, blank=True, on_delete=models.CASCADE)
    medpayPipLeinContact = models.ForeignKey(Contact, related_name='insuranceType_medpayPipLeinContact', null=True, blank=True, on_delete=models.CASCADE)
    propDamContact = models.ForeignKey(Contact, related_name='insuranceType_propDamContact', null=True, blank=True, on_delete=models.CASCADE)
    group_number = models.CharField(max_length=255, null=True, blank=True, default='')
    policy_number = models.CharField(max_length=255, null=True, blank=True, default='')
    claim_number = models.CharField(max_length=255, null=True, blank=True, default='')
    account_number = models.CharField(max_length=255, null=True, blank=True, default='')
    liabilityLimit = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    liabilityLimitAll = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    UMLimit1 = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    UMLimitAll = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    midPayPipLimit = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    propDamLimit = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    lien = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    lienFinal = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    ERISAYN = models.BooleanField(default=False, null=True, blank=True)
    


class RecentCases(models.Model):
    user = models.OneToOneField(User, related_name='recentcases_user', null=False, on_delete=models.CASCADE)
    case_ids = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.user.username)

class Defendant(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=255, null=True, default='', blank=True)
    middle_name = models.CharField(max_length=255, null=True, default='', blank=True)
    last_name = models.CharField(max_length=255, null=True, default='', blank=True)
    home_contact = models.ForeignKey(Contact, related_name='defendant_home_contact', on_delete=models.CASCADE, null=True, blank=True)
    work_contact = models.ForeignKey(Contact, related_name='defendant_work_contact', on_delete=models.CASCADE, null=True, blank=True)
    defendant_employer = models.CharField(max_length=255, null=True, blank=True, default='')
    # address1 = models.CharField(max_length=255, null=True, blank=True, default='')
    # address2 = models.CharField(max_length=255, null=True, blank=True, default='')
    # state = models.CharField(max_length=255, null=True, blank=True, default='')
    # city = models.CharField(max_length=255, null=True, blank=True, default='')
    # post_code = models.CharField(max_length=255, null=True, blank=True, default='')
    # phone = models.CharField(max_length=255, null=True, blank=True, default='')
    # email = models.CharField(max_length=255, null=True, blank=True, default='')
    birthday = models.CharField(max_length=255, null=True, blank=True, default='')
    ssn = models.CharField(max_length=255, null=True, blank=True, default='')
    driver_license = models.CharField(max_length=255, null=True, blank=True, default='')
    age = models.CharField(max_length=255, null=True, blank=True, default='')
    defendant_note = models.CharField(max_length=255, null=True, blank=True, default='')
    defServedDate = models.DateTimeField(null=True, blank=True)
    liability_percent =models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, blank=True)
    liability_insurance_id = models.ManyToManyField(Insurance, related_name='defendant_liability_insurance_id', blank=True)
    defendant_type = models.CharField(max_length=255, null=True, blank=True, default='Private Individual')
    statute_date = models.CharField(max_length=255, null=True, blank=True, default='')
    claim_date = models.CharField(max_length=255, null=True, blank=True, default='')
    expiry_date = models.CharField(max_length=255, null=True, blank=True, default='')
    claim_rejected = models.CharField(max_length=255, null=True, blank=True, default='False')

class Statute(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    for_defendant = models.ForeignKey(Case, related_name='defendant_statutes', on_delete=models.CASCADE, null=True)

    statute_date =  models.DateTimeField(default='')
    time = models.CharField(max_length=255, default='', blank=True, null=True)



class OtherParty(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    party_first_name = models.CharField(max_length=255, null=True, blank=True, default='')
    party_middle_name = models.CharField(max_length=255, null=True, blank=True, default='')
    party_last_name = models.CharField(max_length=255, null=True, blank=True, default='')
    party_home_contact = models.ForeignKey(Contact, related_name='otherparty_home_contact', on_delete=models.CASCADE, null=True, blank=True)
    party_contact_last = models.ForeignKey(Contact, related_name='otherparty_last_contact', on_delete=models.CASCADE, null=True, blank=True)
    party_employer = models.CharField(max_length=255, null=False, default='')
    # address1 = models.CharField(max_length=255, null=False, default='')
    # address2 = models.CharField(max_length=255, null=False, default='')
    # state = models.CharField(max_length=255, null=False, default='')
    # city = models.CharField(max_length=255, null=False, default='')
    # post_code = models.CharField(max_length=255, null=False, default='')
    # phone = models.CharField(max_length=255, null=False, default='')
    # email = models.CharField(max_length=255, null=False, default='')
    party_dob = models.CharField(max_length=255, null=True, default='', blank=True)
    ssn = models.CharField(max_length=255, null=True, default='', blank=True)
    driver_license = models.CharField(max_length=255, null=True, default='', blank=True)
    age = models.CharField(max_length=255, null=True, default='', blank=True)
    party_note = models.CharField(max_length=255, null=True, default='', blank=True)
    party_served_date = models.DateTimeField(null=True, blank=True)
    party_deposition_date = models.DateTimeField(null=True, blank=True)
    other_party_insurance = models.ManyToManyField(Insurance, blank=True)

class Witness(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    witness_first_name = models.CharField(max_length=255, null=False, blank=True, default='')
    witness_middle_name = models.CharField(max_length=255, null=False, blank=True, default='')
    witness_last_name = models.CharField(max_length=255, null=False, blank=True, default='')
    witness_contact_home = models.ForeignKey(Contact, related_name='witness_contact_home', on_delete=models.CASCADE, null=True)
    witness_contact_last = models.ForeignKey(Contact, related_name='witness_last_home', on_delete=models.CASCADE, null=True)
    witness_employer = models.CharField(max_length=255, null=False, default='')
    # address1 = models.CharField(max_length=255, null=False, blank=True, default='')
    # address2 = models.CharField(max_length=255, null=False, blank=True, default='')
    # state = models.CharField(max_length=255, null=False, blank=True, default='')
    # city = models.CharField(max_length=255, null=False, blank=True, default='')
    # post_code = models.CharField(max_length=255, null=False, blank=True, default='')
    # phone = models.CharField(max_length=255, null=False, blank=True, default='')
    # email = models.CharField(max_length=255, null=False, blank=True, default='')
    witness_birthday = models.DateTimeField(null=True, blank=True)
    ssn = models.CharField(max_length=255, null=False, blank=True, default='')
    driver_license = models.CharField(max_length=255, null=False, blank=True, default='')
    age = models.CharField(max_length=255, null=False, blank=True, default='')
    witness_note = models.CharField(max_length=255, null=False, blank=True, default='')
    witness_served_date = models.DateTimeField(null=True, blank=True)
    witness_deposition_date = models.DateTimeField(null=True, blank=True)
    witness_insurance = models.ManyToManyField(Insurance, blank=True)

class Car(models.Model):
    make = models.CharField(max_length=255, null=False, default='')
    model = models.CharField(max_length=255, null=False, default='')
    year = models.CharField(max_length=255, null=False, default='')
    mileage = models.CharField(max_length=255, null=False, default='')
    color = models.CharField(max_length=255, null=False, default='')
    value = models.CharField(max_length=255, null=False, default='')
    locationID = models.CharField(max_length=255, null=False, default='')
    vehicle_note = models.TextField(null=True, blank=True)
    propDamEst = models.CharField(max_length=255, null=False, default='')
    propDamFinal = models.CharField(max_length=255, null=False, default='')

class AccidentType(models.Model):
    name = models.CharField(max_length=255, null=False, default='')
    def __str__(self):
        return str(self.name)

class carAccident(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    contact = models.ForeignKey(Contact, related_name="caraccident_contact", null=True, blank=True, on_delete=models.CASCADE)

    accident_type = models.ForeignKey(AccidentType, on_delete=models.CASCADE, null=True, blank=True)
    accident_note = models.CharField(max_length=255, null=False, default='')
    ambulance = models.BooleanField(null=True, blank=True, default=False)
    emergencyRoom = models.BooleanField(null=True, blank=True, default=False)
    lossOfConc = models.BooleanField(null=True, blank=True, default=False)
    reportTaken = models.BooleanField(null=True, blank=True, default=False)
    ClientCarId = models.ForeignKey(Car, related_name="carAccident_clientcarid", on_delete=models.CASCADE, null=True, blank=True)
    defendantCarId = models.ForeignKey(Car, related_name="carAccident_defendantcarid", on_delete=models.CASCADE, null=True, blank=True)

    # address = models.CharField(max_length=255, null=False, default='')
    # city = models.CharField(max_length=255, null=False, default='')
    # state = models.CharField(max_length=255, null=False, default='')
    date = models.CharField(max_length=255, null=False, default='')
    time = models.CharField(max_length=255, null=False, default='')
    weather = models.CharField(max_length=255, null=False, default='')
    description = models.CharField(max_length=255, null=False, default='')
    lat = models.CharField(max_length=255, null=True, default='')
    long = models.CharField(max_length=255, null=True, default='')

class Litigation(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    jurisdiction = models.CharField(max_length=255, null=True, default='')
    case_name = models.CharField(max_length=255, null=True, default='')
    federal_court = models.CharField(max_length=255, null=True, default='')
    case_number = models.CharField(max_length=255, null=True, default='')
    court_name = models.CharField(max_length=255, null=True, default='')
    court_address1 = models.CharField(max_length=255, null=True, default='')
    court_address2 = models.CharField(max_length=255, null=True, default='')
    court_address_city = models.CharField(max_length=255, null=True, default='')
    court_address_zip = models.CharField(max_length=255, null=True, default='')
    state = models.ForeignKey(State, null=True, related_name='litigation_states', on_delete=models.CASCADE)
    county = models.ForeignKey(County, null=True, related_name='litigation_county', on_delete=models.CASCADE)

    judge_name = models.CharField(max_length=255, null=True, default='')
    judge_contact = models.CharField(max_length=255, null=True, default='')
    department = models.CharField(max_length=255, null=True, default='')
    department_contact = models.CharField(max_length=255, null=True, default='')

class FlaggedPage(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    page_name = models.CharField(max_length=255, null=True, default='')
    flagged_on = models.DateTimeField(auto_now_add=True)
    flagged_by = models.ForeignKey(User, related_name='firm_flaggedcases', on_delete=models.CASCADE, null=True)
    page_link = models.CharField(max_length=255, null=True, default='')

    def __str__(self):
        return self.page_name




class ChequeType(models.Model):
    name = models.CharField(max_length=255, null=True, default='', blank=True)

    def __str__(self):
        return self.name

class BankAccounts(models.Model):
    firm = models.ForeignKey(Attorney, null=True, on_delete=models.CASCADE)
    bank = models.CharField(max_length=255, null=True, default='', blank=True)
    account_name = models.CharField(max_length=255, null=True, default='', blank=True)
    account_number = models.CharField(max_length=255, null=True, default='', blank=True)
    check_types = models.ManyToManyField(ChequeType)


    def __str__(self):
        return self.account_name

# class AttachBankCheque(models.Model):
#     firm = models.ForeignKey(Attorney, null=True, on_delete=models.CASCADE)
#     check_type = models.ForeignKey(ChequeType, null=True, on_delete=models.CASCADE)
#     bank_account = models.ForeignKey(BankAccounts, null=True, on_delete=models.CASCADE)

class Check(models.Model):
    date_requested = models.DateTimeField(auto_now_add=True)
    cheque_date = models.CharField(max_length=255, null=True, default='', blank=True)
    cheque_number = models.CharField(max_length=255, null=True, default='', blank=True)
    amount =models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    payee = models.CharField(max_length=255, null=True, default='', blank=True)
    memo = models.CharField(max_length=255, null=True, default='', blank=True)
    cleared_date = models.CharField(max_length=255, null=True, default='', blank=True)

    bank_account = models.ForeignKey(BankAccounts, null=True, on_delete=models.SET_NULL)
    cheque_type = models.ForeignKey(ChequeType, null=True, on_delete=models.SET_NULL)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)

    created_by = models.ForeignKey(AttorneyStaff, null=True, on_delete=models.SET_NULL)
class Costs(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    cheque = models.ForeignKey(Check, null=True, on_delete=models.SET_NULL)
    date = models.CharField(max_length=255, null=True, default='')
    paid_by = models.CharField(max_length=255, null=True, default='', blank=True)
    invoice_number = models.CharField(max_length=255, null=True, default='')
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    final_amount = models.DecimalField(decimal_places=2, max_digits=10, null=True)

    document = models.OneToOneField(Doc, related_name='costs_doc', null=True, on_delete=models.SET_NULL)


class ToDo(models.Model):
    created_by = models.ForeignKey(User, related_name='todo_users', null=True, on_delete=models.CASCADE)
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    due_date = models.CharField(max_length=255, null=True, default='')
    time = models.CharField(max_length=255, null=True, default='', blank=True)
    # user_type = models.ForeignKey(AttorneyUserType, related_name='Todo_usertypes', null=True, on_delete=models.SET_NULL)
    todo_for = models.ForeignKey(AttorneyStaff, related_name='for_todo_users', null=True, on_delete=models.CASCADE)
    todo_type = models.CharField(max_length=255, null=True, blank=True, default='')
    notes = models.CharField(max_length=255, null=True, blank=True, default='N/A')
    status = models.CharField(max_length=255, null=True, blank=True, default='Not Completed')

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    completed_at = models.CharField(max_length=255, null=True, blank=True, default='')
    completed_note = models.CharField(max_length=255, null=True, blank=True, default='')

    last_updated = models.DateTimeField(null=True, blank=True)
    days_to_repeat = models.IntegerField(default=0, null=True, blank=True)
    case_status = models.ManyToManyField(Status, blank=True)
    


class LetterTemplate(models.Model):
    template = models.FileField(upload_to='images/', null=True)
    template_name = models.CharField(max_length=255, null=True, default='')
    template_type = models.CharField(max_length=255, null=True, default='')

class CourtForms(models.Model):
    form = models.FileField(upload_to='images/', null=True)
    key = models.FileField(upload_to='images/', null=True)
    form_name = models.CharField(max_length=255, null=True, default='')
    for_state = models.ForeignKey(State, null=True, related_name='courtform_states', on_delete=models.CASCADE)
    for_county = models.ForeignKey(County, null=True, related_name='courtform_counties', on_delete=models.CASCADE)
    def __str__(self):
        return self.form_name

class Variables(models.Model):
    name =  models.CharField(max_length=255, null=True, default='')
    description = models.TextField(null=True)
    value = models.CharField(max_length=255, null=True, default='')

    def __str__(self):
        return self.name



class CaseChecklist(models.Model):
    checklist = models.ForeignKey(CheckList, on_delete=models.CASCADE, null=True, related_name='orignalchecklist_case')
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    status = models.BooleanField(null=True, default=False)

    
class PanelCheckList(models.Model):
    panel_name = models.ForeignKey(Page, related_name='panel_checklist_page', null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, default='')
   

    def __str__(self):
        return self.name

class PanelCaseChecklist(models.Model):
    checklist = models.ForeignKey(PanelCheckList, on_delete=models.CASCADE, null=True, related_name='panelorignalchecklist_case')
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    for_provider = models.ForeignKey(CaseProviders, on_delete=models.CASCADE, null=True)
    for_defendant = models.ForeignKey(Defendant, on_delete=models.CASCADE, null=True)
    for_witness = models.ForeignKey(Witness, on_delete=models.CASCADE, null=True)
    for_otherparty = models.ForeignKey(OtherParty, on_delete=models.CASCADE, null=True)
    status = models.BooleanField(null=True, default=False)


class CaseLoan(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    application_date = models.CharField(max_length=255, null=True, default='')
    loan_company = models.CharField(max_length=255, null=True, default='')
    contact_name = models.CharField(max_length=255, null=True, default='')
    contact = models.ForeignKey(Contact, related_name='caseloans_contact', null=True, blank=True, on_delete=models.CASCADE)
    # phone = models.CharField(max_length=255, null=True, default='')

    # address1 = models.CharField(max_length=255, null=True, default='')
    # address2 = models.CharField(max_length=255, null=True, default='')
    # city = models.CharField(max_length=255, null=True, default='')
    # state = models.CharField(max_length=255, null=True, default='')
    # zip_code = models.CharField(max_length=255, null=True, default='')
    
    # email = models.CharField(max_length=255, null=True, default='')
    # loan_amount = models.CharField(max_length=255, null=True, default='')
    fees = models.IntegerField(default=0, null=True)
    status = models.CharField(max_length=255, null=True, default='')
    interest = models.CharField(max_length=255, null=True, default='')
    amount_estimate = models.IntegerField(default=0, null=True)
    current_amount_verified = models.IntegerField(default=0, null=True)
    date_verified = models.CharField(max_length=255, null=True, default='')

    final_amount = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    check_number = models.CharField(max_length=255, null=True, default='')




class Discovery(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True)
    date_served = models.CharField(max_length=255, null=True, default='')
    due_date = models.CharField(max_length=255, null=True, default='')
    description = models.TextField(null=True)
    type = models.CharField(max_length=255, null=True, default='')
    from_defendant = models.ForeignKey(Defendant, related_name='give_by_defendant', on_delete=models.CASCADE, null=True)
    to_defendant = models.ForeignKey(Defendant, on_delete=models.CASCADE, null=True)


class Injuries(models.Model):
    name = models.CharField(max_length=255, null=True, default='')
    value = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.name)

class Injury(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='injury_cases', on_delete=models.CASCADE, null=True)
    injury = models.ForeignKey(Injuries, on_delete=models.CASCADE, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, default='')
    # location = models.ForeignKey(Location, related_name='injury_location', null=True, on_delete=models.CASCADE)
    # specialty = models.ForeignKey(Specialty, related_name='injury_specialty', null=True, on_delete=models.CASCADE)
    provider = models.ForeignKey(CaseProviders, related_name='injury_provider', null=True, on_delete=models.CASCADE)

class Deposition(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='deposition_cases', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255, null=True, default='')
    date = models.CharField(max_length=255, null=True, default='')
    time = models.CharField(max_length=255, null=True, default='')
    defending = models.ForeignKey(Defendant, related_name='deposition_defendants', on_delete=models.SET_NULL, null=True)
    taking = models.CharField(max_length=255, null=True, default='')
    location = models.CharField(max_length=255, null=True, default='')
    address1 = models.CharField(max_length=255, null=True, default='')
    address2 = models.CharField(max_length=255, null=True, default='')
    city = models.CharField(max_length=255, null=True, default='')
    state = models.CharField(max_length=255, null=True, default='')
    zip_code = models.CharField(max_length=255, null=True, default='')
    note = models.TextField(null=True)

class Offer(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='offer_cases', on_delete=models.CASCADE, null=True)
    date = models.CharField(max_length=255, null=True, default='')
    note = models.CharField(max_length=255, null=True, default='')
    check_number = models.IntegerField(null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    final_amount = models.CharField(max_length=255, null=True, default='')

class Fees(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='fees_cases', on_delete=models.CASCADE, null=True)
    note = models.CharField(max_length=255, null=True, default='')
    check_number = models.IntegerField(null=True)
    percentage = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    final_amount = models.DecimalField(decimal_places=2, max_digits=10, null=True)

class ClientProceeds(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='client_proceeds_cases', on_delete=models.CASCADE, null=True)
    check_number = models.IntegerField(null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    cleared = models.CharField(max_length=255, null=True, default='')
    check_date = models.CharField(max_length=255, null=True, default='')
    name_on_check = models.CharField(max_length=255, null=True, default='')
    
    

class IncidentReport(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='case_incident_report', on_delete=models.CASCADE, null=True)
    reporting_agency = models.CharField(max_length=255, null=True, default='', blank=True)
    officer_first_name = models.CharField(max_length=255, null=True, default='', blank=True)
    officer_last_name = models.CharField(max_length=255, null=True, default='', blank=True)
    address1 = models.CharField(max_length=255, null=True, default='', blank=True)
    address2 = models.CharField(max_length=255, null=True, default='', blank=True)
    city = models.CharField(max_length=255, null=True, default='', blank=True)
    state = models.CharField(max_length=255, null=True, default='', blank=True)
    zip_code = models.CharField(max_length=255, null=True, default='', blank=True)
    report_number = models.CharField(max_length=255, null=True, default='', blank=True)
    phone = models.CharField(max_length=255, null=True, default='', blank=True)
    email = models.CharField(max_length=255, null=True, default='', blank=True)
    fax = models.CharField(max_length=255, null=True, default='', blank=True)
    website = models.CharField(max_length=255, null=True, default='', blank=True)
    cost = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    check_number = models.CharField(max_length=255, null=True, default='', blank=True)

    cheque = models.ForeignKey(Check, null=True, on_delete=models.SET_NULL)
    payee = models.CharField(max_length=255, null=True, default='', blank=True)

class IncidentNotes(models.Model):
    for_incident = models.ForeignKey(IncidentReport, null=True, related_name='incident_report_notes', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ReportingAgency(models.Model):
    # for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    # for_case = models.ForeignKey(Case, related_name='police_report_cases', on_delete=models.CASCADE, null=True)
    # for_agency = models.ForeignKey(IncidentReport, related_name='incident_policereports', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255, null=True, default='')
    payee = models.CharField(max_length=255, null=True, default='')
    address = models.CharField(max_length=255, null=True, default='')
    address1 = models.CharField(max_length=255, null=True, default='', blank=True)
    city = models.CharField(max_length=255, null=True, default='', blank=True)
    state = models.CharField(max_length=255, null=True, default='', blank=True)
    zip_code = models.CharField(max_length=255, null=True, default='', blank=True)
    phone = models.CharField(max_length=255, null=True, default='', blank=True)
    extension = models.CharField(max_length=255, null=True, default='', blank=True)
    fax = models.CharField(max_length=255, null=True, default='', blank=True)
    email = models.CharField(max_length=255, null=True, default='', blank=True)
    website = models.CharField(max_length=255, null=True, default='', blank=True)

class LitigationDetails(models.Model):
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='case_hearings', on_delete=models.CASCADE, null=True)
    date = models.CharField(max_length=255, null=True, default='', blank=True)
    end_date = models.CharField(max_length=255, null=True, default='', blank=True)
    time = models.CharField(max_length=255, null=True, default='', blank=True)
    end_time = models.CharField(max_length=255, null=True, default='', blank=True)
    description = models.TextField(null=True, blank=True)
    department = models.CharField(max_length=255, null=True, default='')
    litigation_type = models.CharField(max_length=255, null=True, default='')
    zoom_link = models.TextField(null=True, blank=True)


class TFNotes(models.Model):
    for_provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    for_case = models.ForeignKey(Case, related_name='tf_notes_case', on_delete=models.CASCADE, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    description = models.TextField(null=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TFTodos(models.Model):
    created_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    for_case = models.ForeignKey(Case, related_name='tf_todo_case', on_delete=models.CASCADE, null=True)
    due_date = models.CharField(max_length=255, null=True, default='')
    
    todo_for = models.ForeignKey(User, related_name='todo_for_user', null=True, on_delete=models.CASCADE)
    todo_type = models.CharField(max_length=255, null=True, blank=True, default='')
    notes = models.CharField(max_length=255, null=True, blank=True, default='N/A')
    status = models.CharField(max_length=255, null=True, blank=True, default='Not Completed')

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    completed_at = models.CharField(max_length=255, null=True, blank=True, default='')
    completed_note = models.CharField(max_length=255, null=True, blank=True, default='')


# class ChequeRequests(models.Model):
#     for_case = models.ForeignKey(Case, related_name='case_checkrequests', on_delete=models.CASCADE, null=True)
    
#     requested_by = models.ForeignKey(AttorneyStaff, related_name='firm_users_chequerequests', null=True, on_delete=models.CASCADE)
#     cheque_type = models.CharField(max_length=255, null=True, default='', blank=True    )
    
#     cleared_on = models.CharField(max_length=255, null=True, default='', blank=True)
#     cost = models.CharField(max_length=255, null=True, default='', blank=True)
#     incident_report = models.ForeignKey(IncidentReport, null=True, on_delete=models.CASCADE)




# class Click(models.Model):
#     click_id = models.IntegerField(default=0, null=True, blank=True)
#     for_page = models.ForeignKey(Page, related_name='click_record_page', on_delete=models.CASCADE, null=True, blank=True)
#     clickIDName = models.CharField(max_length=255, null=True, blank=True, default='')

#     def __str__(self):
#         return str(self.click_id)

class ClickRecord(models.Model):
    click = models.IntegerField(default=0, null=True, blank=True)
    user = models.ForeignKey(User, related_name='click_record_user', on_delete=models.CASCADE, null=True)
    for_firm = models.ForeignKey(Attorney, related_name='click_record_attorney', on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey(Case, related_name='click_record_case', on_delete=models.CASCADE, null=True)
    for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    for_page = models.ForeignKey(Page, related_name='click_record_page', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# class ClickLog(models.Model):
#     click = models.IntegerField(default=0, null=True, blank=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
#     for_firm = models.ForeignKey(Attorney,  on_delete=models.CASCADE, null=True)
#     for_case = models.ForeignKey(Case,  on_delete=models.CASCADE, null=True)
#     for_client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
#     for_page = models.ForeignKey(Page, on_delete=models.CASCADE, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
    

class TreatmentGap(models.Model):
    for_case = models.ForeignKey(Case, related_name='tf_gap_case', on_delete=models.CASCADE, null=True)
    for_case_provider = models.ForeignKey(CaseProviders, related_name='tf_gap_case_providers', on_delete=models.CASCADE, null=True)
    first_date = models.CharField(max_length=255, null=True, blank=True, default='')
    second_date = models.CharField(max_length=255, null=True, blank=True, default='')
    note = models.CharField(max_length=255, null=True, blank=True, default='')
    days = models.IntegerField(default=0, null=True, blank=True)
    doc = models.ForeignKey(Doc, related_name='tf_gap_doc', on_delete=models.CASCADE, null=True)


class ThreadManager(models.Manager):
    def by_user(self, **kwargs):
        user = kwargs.get('user')
        lookup = Q(first_person=user) | Q(second_person=user)
        qs = self.get_queryset().filter(lookup).distinct()
        return qs


class Thread(models.Model):
    first_person = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='thread_first_person')
    second_person = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='thread_second_person')
    updated = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = ThreadManager()

    class Meta:
        unique_together = ['first_person', 'second_person']

class ChatMessage(models.Model):
    thread = models.ForeignKey(Thread, null=True, blank=True, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sender_name = models.CharField(max_length=255, null=True, blank=True, default='')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)



class Emails(models.Model):
    for_case = models.ForeignKey(Case, related_name='email_case', on_delete=models.CASCADE, null=True)
    for_client = models.ForeignKey(Client, related_name='email_client', on_delete=models.CASCADE, null=True)
    created_by = models.ForeignKey(User, related_name='email_created_by', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    body = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

# class ThresholdField(models.Model):
#     name = models.CharField(max_length=255, null=True, blank=True, default='')
#     value = models.CharField(max_length=255, null=True, blank=True, default='')
#     min = models.CharField(max_length=255, null=True, blank=True, default='')
#     max models.CharField(max_length=255, null=True, blank=True, default='')

#     def __str__(self):
#         return self.name

class FirmThresholdValue(models.Model):
    for_firm = models.OneToOneField(Attorney, related_name='firm_threshold_values', on_delete=models.CASCADE, null=True)
    property_damage_value = models.CharField(max_length=255, null=True, blank=True, default='')
    property_damage_value_min = models.CharField(max_length=255, null=True, blank=True, default='')
    property_damage_value_max = models.CharField(max_length=255, null=True, blank=True, default='')
    

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# jairo

def update_filename(instance, filename):
    path_you_want_to_upload_to = "doc_templates/"
    return os.path.join(path_you_want_to_upload_to, filename.lower())


class Doc_Template(models.Model):
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE)
    x_coord = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10000)], default=13)
    y_coord = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10000)], default=24)
    FONT_CHOICES =(('Courier', 'Courier'), ('Helvetica', 'Helvetica'), ('Times', 'Times'))
    font = models.CharField(choices=FONT_CHOICES, max_length=9, default='Helvetica')
    font_size = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10000)], default=12)
    line_spacing = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10000)], default=7)
    target_page = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    template = models.FileField(upload_to=update_filename, null=True, validators=[FileExtensionValidator(['pdf'])], default='doc_templates/alignment_test_template.pdf')
    template_stamped = models.FileField(upload_to=update_filename, null=True, blank=True, validators=[FileExtensionValidator(['pdf'])] )
    should_update_stamp = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        try:
            this = Doc_Template.objects.get(id=self.id)
            if this.template != self.template:
                this.template.delete(save=False)
            if this.template_stamped != self.template_stamped:
                this.template_stamped.delete(save=False)
        except: pass
        super(Doc_Template, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.pk)


def Doc_Template_pre_save(sender, instance, *args, **kwargs):
    # validates if any field has been changed, if so the Doc_Template_post_save function will update the template_stamped file 

    try:    
        old_instance = Doc_Template.objects.get(id=instance.id)
        
        keys = ['x_coord', 'y_coord', 'font', 'font_size', 'line_spacing', 'target_page', 'template']

        new_instance_fields= instance.__dict__
        new_instance_values = list( map(new_instance_fields.get, keys) )

        old_instance_fields= old_instance.__dict__
        old_instance_values = list( map(old_instance_fields.get, keys) )
        
        if(old_instance_values!=new_instance_values):
            instance.should_update_stamp = True
    
    except Exception as e:
        print(e)
        instance.should_update_stamp = True


def Doc_Template_post_save(sender, instance, *args, **kwargs):
    # updates the template_stamped file

    text1="Medical Provider Name"
    text2="Address 1"
    text3="Address 2"
    text4="City"
    text5="State"
    text6="Zip Code"

    instance.should_update_stamp = not instance.should_update_stamp
    
    if not instance.should_update_stamp:
        create_stamped_file(
            X=instance.x_coord, 
            Y=instance.y_coord, 
            Font=instance.font,
            Size=instance.font_size,
            LineSpacing=instance.line_spacing,
            target_page=instance.target_page,
            Text=[text1, text2, text3, text4, text5, text6],
            instance=instance
        )

pre_save.connect(Doc_Template_pre_save, sender=Doc_Template)
post_save.connect(Doc_Template_post_save, sender=Doc_Template)


def Doc_stamp_HIPAA_file(sender, instance, *args, **kwargs):
    # stamps the uploaded HIPAA file

    # http://127.0.0.1:8000/admin/accounts/location/11/change/
    # http://127.0.0.1:8000/admin/BP/doc_template/3/change/
    # http://127.0.0.1:8000/admin/BP/doc/815/change/

    try:
        instance_upload_name = instance.upload.name.split("/")[1]
        if instance.document_no == "HIPAA" and "__stamped.pdf" not in instance_upload_name:
            location = Location.objects.get(pk=11)
            doc_template = Doc_Template.objects.get(pk=3)
        
            text1=str(location.added_by)
            text2=location.address
            text3=location.address2
            text4=location.city
            text5=location.state
            text6=location.post_code

            create_stamped_file(
                X=doc_template.x_coord, 
                Y=doc_template.y_coord, 
                Font=doc_template.font,
                Size=doc_template.font_size,
                LineSpacing=doc_template.line_spacing,
                target_page=doc_template.target_page,
                Text=[text1, text2, text3, text4, text5, text6],
                instance=instance,
                HIPAA_file=True
            )
    except Exception as e:
        print(e)

post_save.connect(Doc_stamp_HIPAA_file, sender=Doc)