from csv import list_dialects
from django.contrib import admin
from .models import AttorneyStaff, Favorite, Flagged, Location, Marketer, MarketerStaff, ProviderStaff, Specialty, Doctor, OtherLocations, Review, Provider, Attorney, AttorneyLocation, TFAccounting, TFCaseStatus, TFDoc, TFTreatmentDate
# Register your models here.


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['address', 'added_by']

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'radius', 'color']

@admin.register(Review)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'given_to']

    def name(self, review):
        return review.given_by.attorneyprofile.first_name

@admin.register(Provider)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['officename', 'accounttype', 'firstname']

    def officename(self, provider):
        return provider.providerprofile.office_name

    def accounttype(self, provider):
        return provider.providerprofile.account_type

    def firstname(self, provider):
        return provider.providerprofile.first_name



@admin.register(Attorney)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['officename', 'accounttype', 'firstname']

    def officename(self, attorney):
        return attorney.attorneyprofile.office_name

    def accounttype(self, attorney):
        return attorney.attorneyprofile.account_type

    def firstname(self, attorney):
        return attorney.attorneyprofile.first_name


admin.site.register(Doctor)
admin.site.register(OtherLocations)
admin.site.register(Marketer)
admin.site.register(Favorite)
admin.site.register(Flagged)

admin.site.register(ProviderStaff)
admin.site.register(AttorneyStaff)
admin.site.register(MarketerStaff)
admin.site.register(TFTreatmentDate)
admin.site.register(TFAccounting)
admin.site.register(TFCaseStatus)
admin.site.register(TFDoc)


