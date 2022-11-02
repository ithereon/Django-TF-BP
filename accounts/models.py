from django.db import models
from django.contrib.auth.models import User


class Firm(models.Model):
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=False, null=False, default='')
    last_name = models.CharField(max_length=100, blank=False, null=False, default='')
    email = models.CharField(max_length=200, default='NA', null=False)
    account_type = models.CharField(max_length=100, blank=False, null=False, default='')
    office_name = models.CharField(max_length=255, blank=False, null=False, default='')

    
class Provider(models.Model):

    providerprofile = models.ForeignKey(Firm, related_name='provider_userprofile', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    website = models.CharField(null=True, default='', blank=True, max_length=255)
    fb_page = models.CharField(null=True, default='', blank=True, max_length=255)
    twitter_page = models.CharField(null=True, default='', blank=True, max_length=255)
    google_page = models.CharField(null=True, default='', blank=True, max_length=255)
    review_percentage = models.IntegerField(null=True, default=0)
    


    def __str__(self):
        return self.providerprofile.office_name



class ProviderStaff(models.Model):
    created_by = models.ForeignKey(Provider, on_delete=models.CASCADE)
    user = models.OneToOneField(User, related_name='providerstaff_userprofile',null=True, on_delete=models.CASCADE)
    account_type = models.CharField(null=False, default='ProviderStaff', max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    permission = models.CharField(default='No', max_length=255, null=True, blank=True)

class Specialty(models.Model):
    name = models.TextField(null=False, default='')
    radius = models.IntegerField(default=0, null=False)
    color = models.CharField(max_length=255, null=True)
    secondary_color = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name


class Location(models.Model):

    added_by = models.ForeignKey(Provider, related_name='location_userprofile', on_delete=models.CASCADE)
    address = models.CharField(verbose_name="Address1",max_length=100, null=True, blank=True, default='')
    address2 = models.CharField(verbose_name="Address2",max_length=100, null=True, blank=True, default='')
    city = models.CharField(verbose_name="City",max_length=100, null=True, blank=True, default='')
    state = models.CharField(verbose_name="State",max_length=100, null=True, blank=True, default='')
    post_code = models.CharField(verbose_name="Post Code",max_length=8, null=True, blank=True, default='')
    country = models.CharField(verbose_name="Country",max_length=100, null=True, blank=True, default='')
    longitude = models.CharField(verbose_name="Longitude",max_length=50, null=True, blank=True)
    latitude = models.CharField(verbose_name="Latitude",max_length=50, null=True, blank=True)

    phone = models.CharField(verbose_name="Phone",max_length=100, null=True, blank=True)
    fax = models.CharField(verbose_name="Fax",max_length=100, null=True, blank=True)
    email = models.CharField(verbose_name="Email",max_length=100, null=True, blank=True)

    specialties = models.ManyToManyField(Specialty, related_name='loc_specialty')

    def __str__(self):
        return str(self.address)


class Favorite(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.provider.providerprofile.office_name

class Flagged(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, null=True)
    description = models.TextField(null=True)

class TFTreatmentDate(models.Model):
    created_by = models.ForeignKey(Provider, related_name='created_by_tf', on_delete=models.CASCADE)
    for_case_provider = models.ForeignKey('BP.CaseProviders', related_name='case_provider_treatmentdate', on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey('BP.Case', related_name='case_tftreatmentdate', on_delete=models.CASCADE, null=True)
    # location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='tf_provider_location')
    # specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name='tf_provider_specialty')
    first_date = models.CharField(null=True, default='_/_/_', blank=True, max_length=255)
    second_date = models.CharField(null=True, default='_/_/_', blank=True, max_length=255)
    visits = models.CharField(null=True, default='__', blank=True, max_length=255)

class TFAccounting(models.Model):
    created_by = models.ForeignKey(Provider, related_name='created_by_tf_accounting', on_delete=models.CASCADE)
    for_case_provider = models.ForeignKey('BP.CaseProviders', related_name='case_provider_accounting', on_delete=models.CASCADE, null=True)
    for_case = models.ForeignKey('BP.Case', related_name='case_tfaccounting', on_delete=models.CASCADE, null=True)
    original = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    hi_paid = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    hi_reduction = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    mp_paid = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    patient_payment_value = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    reduction = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    liens = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    final = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    payments = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)
    reductions = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True, default=0.00)

    check_number = models.CharField(max_length=255, null=True, blank=True, default='')
    payment_received_date = models.CharField(null=True, default='_/_/_', blank=True, max_length=255)

class TFDoc(models.Model):
    for_provider = models.ForeignKey(Provider, related_name='created_by_tf_accounting_doc', on_delete=models.CASCADE)
    for_tf_accounting = models.ForeignKey(TFAccounting, related_name='tf_accounting_doc', null=True, on_delete=models.CASCADE)
    upload = models.FileField(upload_to='images/', null=True)
    file_name = models.CharField(max_length=255, null=True, blank=True, default='')
    page_name = models.CharField(max_length=255, null=True, blank=True, default='')
    document_no = models.CharField(max_length=255, null=True, blank=True, default='')
    check = models.CharField(max_length=255, null=True, blank=True, default='False')

    def __str__(self):
        return str(self.pk)

class TFCaseStatus(models.Model):
    name = models.CharField(null=True, blank=True, max_length=255)
    order = models.IntegerField(default=0, null=True)

    class Meta:
        ordering = ('order', )

    def __str__(self):
        return self.name


class Attorney(models.Model):
    attorneyprofile = models.ForeignKey(Firm, related_name='attorney_userprofile', on_delete=models.CASCADE)
    favorites = models.ManyToManyField(Favorite, related_name='fav_providers')
    blacklist = models.ManyToManyField(Provider, related_name='black_providers')
    flag = models.ManyToManyField(Flagged, related_name='flag_providers')
    marketer_code = models.CharField(max_length=255, null=True)


    def __str__(self):
        return self.attorneyprofile.office_name

class AttorneyStaff(models.Model):
    created_by = models.ForeignKey(Attorney, on_delete=models.CASCADE)
    user = models.OneToOneField(User, related_name='attorneystaff_userprofile',null=True, on_delete=models.CASCADE)
    account_type = models.CharField(null=False, default='AttorneyStaff', max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class Marketer(models.Model):
    marketerprofile = models.ForeignKey(Firm, related_name='marketer_userprofile', on_delete=models.CASCADE)
    favorites = models.ManyToManyField(Favorite, related_name='favmarketer_providers')
    blacklist = models.ManyToManyField(Provider, related_name='blackmarketer_providers')
    flag = models.ManyToManyField(Provider, related_name='flagmarketer_providers')

    marketer_code = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.marketerprofile.office_name

class MarketerStaff(models.Model):
    created_by = models.ForeignKey(Marketer, on_delete=models.CASCADE)
    user = models.OneToOneField(User, related_name='marketerstaff_userprofile',null=True, on_delete=models.CASCADE)
    account_type = models.CharField(null=False, default='MarketerStaff', max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    given_to = models.ForeignKey(Provider, related_name='review_userprofile', on_delete=models.CASCADE)
    given_by = models.ForeignKey(Attorney,null=True, related_name='reviews_attorney', on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=5,decimal_places=2, null=False, default=0)
    description = models.TextField(null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    post_as = models.CharField(max_length=255, default='', null=True)


    def __str__(self):
        return self.given_by.attorneyprofile.first_name


class MarketerLocation(models.Model):
    added_by = models.ForeignKey(Marketer, related_name='location_marketer', on_delete=models.CASCADE)
    address = models.CharField(verbose_name="Address1",max_length=100, null=True, blank=True, default='')
    address2 = models.CharField(verbose_name="Address2",max_length=100, null=True, blank=True, default='')
    city = models.CharField(verbose_name="City",max_length=100, null=True, blank=True, default='')
    state = models.CharField(verbose_name="State",max_length=100, null=True, blank=True, default='')
    post_code = models.CharField(verbose_name="Post Code",max_length=8, null=True, blank=True, default='')
    country = models.CharField(verbose_name="Country",max_length=100, null=True, blank=True, default='')
    phone = models.CharField(verbose_name="Phone",max_length=100, null=True, blank=True)
    fax = models.CharField(verbose_name="Fax",max_length=100, null=True, blank=True)
    email = models.CharField(verbose_name="Email",max_length=100, null=True, blank=True)



class AttorneyLocation(models.Model):
    added_by = models.ForeignKey(Attorney, related_name='location_attorney', on_delete=models.CASCADE)
    address = models.CharField(verbose_name="Address1",max_length=100, null=True, blank=True, default='')
    address2 = models.CharField(verbose_name="Address2",max_length=100, null=True, blank=True, default='')
    city = models.CharField(verbose_name="City",max_length=100, null=True, blank=True, default='')
    state = models.CharField(verbose_name="State",max_length=100, null=True, blank=True, default='')
    post_code = models.CharField(verbose_name="Post Code",max_length=8, null=True, blank=True, default='')
    country = models.CharField(verbose_name="Country",max_length=100, null=True, blank=True, default='')
    phone = models.CharField(verbose_name="Phone",max_length=100, null=True, blank=True)
    fax = models.CharField(verbose_name="Fax",max_length=100, null=True, blank=True)
    email = models.CharField(verbose_name="Email",max_length=100, null=True, blank=True)






class OtherLocations(models.Model):
    for_provider = models.ForeignKey(Provider, related_name='other_locations', null=True, on_delete=models.CASCADE)
    address = models.CharField(verbose_name="Address1",max_length=100, null=True, blank=True, default='')
    address2 = models.CharField(verbose_name="Address2",max_length=100, null=True, blank=True, default='')
    city = models.CharField(verbose_name="City",max_length=100, null=True, blank=True, default='')
    state = models.CharField(verbose_name="State",max_length=100, null=True, blank=True, default='')
    post_code = models.CharField(verbose_name="Post Code",max_length=8, null=True, blank=True, default='')
    phone = models.CharField(max_length=255, null=True)
    fax = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    address_type = models.CharField(max_length=255, null=True)

    def __str__(self):
        return str(self.address)



class Doctor(models.Model):
    created_by = models.ForeignKey(Provider, related_name='doctors_userprofile', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    location = models.ForeignKey(Location, related_name="doctor_locations", null=True, on_delete=models.SET_NULL)
    specialties = models.ManyToManyField(Specialty, related_name='doc_specialty')

    def __str__(self):
            return self.first_name





# class TrackSearch(models.Model):
#     ip_address = models.CharField(max_length=255, null=True, black=True)
#     search_made = models.DateTimeField(auto_now_add=True)
#     username = models.CharField(max_length=255, null=True, blank=True)
#     search_type = models.CharField(max_length=255, null=True, blank=True)


