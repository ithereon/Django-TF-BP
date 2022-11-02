
from django.contrib import admin

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import AccidentType, ActCaseStage, ActCaseStatus, Adjuster, Attorney, AttorneyLocation, AttorneyStaff, AttorneyUserType,Act, Car,  CaseStage, Company, Contact, EmergencyContact, FactorScale, Factors, FirmRank, FirmThresholdValue, Injuries, Injury, InsuranceType, Rank, RecentCases, Status, BPAccounting, BankAccounts, CaseChecklist, CaseLoan, Stage, CaseType, Check, CheckList, ChequeType, ClickRecord, Client, CaseProviders, Case, ClientLocation, ClientStatus, Costs, County, CourtForms, Emails, Firm, HIPAADoc, IncidentReport, Insurance, LetterTemplate, LitigationDetails, Notes, Defendant, OtherParty, Page, PanelCaseChecklist, PanelCheckList, ReportingAgency, RequestUpdate, Statute, TFNotes, TFTodos, ToDo, TreatmentDates, TreatmentGap, Variables, Witness, WorkUnit, carAccident, Litigation, Doc, ocr_Page, FlaggedPage, State, ChatMessage, Thread
# Register your models here.

@admin.register(Attorney)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['officename', 'accounttype', 'firstname']

    def officename(self, attorney):
        return attorney.attorneyprofile.office_name

    def accounttype(self, attorney):
        return attorney.attorneyprofile.account_type

    def firstname(self, attorney):
        return attorney.attorneyprofile.first_name

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['id','incident_date', 'Client', 'case_type', 'case_status', 'case_category']

    def Client(self, case):
        return str(case.for_client.first_name + ' ' + case.for_client.last_name)

@admin.register(Notes)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['category', 'created_at', 'Client', 'description']

    def Client(self, note):
        return str(note.for_client.first_name + ' ' + note.for_client.last_name)

# @admin.register(CaseProviders)
# class NoteAdmin(admin.ModelAdmin):
#     list_display = ['Provider', 'Location', 'Specialty', 'Case']

#     def Provider(self, case):
#         return str(case.location.added_by.providerprofile.office_name)

#     def Location(self, case):
#         return case.location.city

#     def Specialty(self, case):
#         return case.specialty.name

#     def Case(self, case):
#         return case.for_case.incident_date

@admin.register(Client)
class Client(admin.ModelAdmin):
    list_display = ['id','Name', 'birthday', 'Created_by']

    def Name(request, client):
        return str(client.first_name + ' ' + client.last_name)
    
    def Created_by(request, client):
        temp = 'No Attorney Attached'
        if client.created_by:
            temp = client.created_by.attorneyprofile.office_name
        return temp

@admin.register(CaseStage)
class CaseStage(admin.ModelAdmin):
    list_display = ['name', 'order']

admin.site.register(FirmThresholdValue)
admin.site.register(AttorneyStaff)
admin.site.register(CaseProviders)
admin.site.register(Defendant)
admin.site.register(OtherParty)
admin.site.register(Witness)
admin.site.register(Insurance)
admin.site.register(carAccident)
admin.site.register(Litigation)
admin.site.register(Doc)
admin.site.register(ocr_Page)
admin.site.register(FlaggedPage)
admin.site.register(TreatmentDates)
admin.site.register(Costs)
admin.site.register(ToDo)
admin.site.register(Firm)
admin.site.register(AttorneyLocation)
admin.site.register(ClientStatus)
admin.site.register(AttorneyUserType)
admin.site.register(LetterTemplate)
admin.site.register(Variables)
admin.site.register(CheckList)
admin.site.register(CaseChecklist)
admin.site.register(Page)
admin.site.register(PanelCheckList)
admin.site.register(PanelCaseChecklist)
admin.site.register(ClientLocation)
admin.site.register(CaseLoan)
admin.site.register(State)
admin.site.register(County)
admin.site.register(CourtForms)
admin.site.register(CaseType)
admin.site.register(IncidentReport)
admin.site.register(ReportingAgency)
admin.site.register(Check)
admin.site.register(ChequeType)
admin.site.register(BankAccounts)
admin.site.register(LitigationDetails)
admin.site.register(Statute)
admin.site.register(TFNotes)
admin.site.register(TFTodos)
admin.site.register(RecentCases)
admin.site.register(RequestUpdate)
admin.site.register(BPAccounting)

admin.site.register(TreatmentGap)
admin.site.register(HIPAADoc)

@admin.register(ClickRecord)
class ClickRecord(admin.ModelAdmin):
    list_display = ['click', 'user', 'firm_name', 'for_case', 'for_client', 'for_page', 'created_at']

    def firm_name(self, obj):
        return str(obj.for_client.created_by.attorneyprofile.office_name)

@admin.register(Stage)
class Stage(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Status)
class Status(admin.ModelAdmin):
    list_display = ['name']

@admin.register(WorkUnit)
class WorkUnit(admin.ModelAdmin):
    list_display = ['wu_name', 'table', 'field']

@admin.register(Act)
class Act(admin.ModelAdmin):
    list_display = ['act_name']

class ChatMessage(admin.TabularInline):
    model = ChatMessage


class ThreadForm(forms.ModelForm):
    def clean(self):
        """
        This is the function that can be used to
        validate your model data from admin
        """
        super(ThreadForm, self).clean()
        first_person = self.cleaned_data.get('first_person')
        second_person = self.cleaned_data.get('second_person')

        lookup1 = Q(first_person=first_person) & Q(second_person=second_person)
        lookup2 = Q(first_person=second_person) & Q(second_person=first_person)
        lookup = Q(lookup1 | lookup2)
        qs = Thread.objects.filter(lookup)
        if qs.exists():
            raise ValidationError(f'Thread between {first_person} and {second_person} already exists.')


class ThreadAdmin(admin.ModelAdmin):
    inlines = [ChatMessage]
    class Meta:
        model = Thread


admin.site.register(Thread, ThreadAdmin)
admin.site.register(Emails)
admin.site.register(ActCaseStatus)
admin.site.register(ActCaseStage)
admin.site.register(Injury)
admin.site.register(Factors)
admin.site.register(EmergencyContact)
admin.site.register(Rank)
admin.site.register(FirmRank)

class ContactAdmin(admin.ModelAdmin):
        list_display = ['address1','address2','city','state', 'phone_number', 'email']

admin.site.register(Contact, ContactAdmin)
admin.site.register(Car)

admin.site.register(InsuranceType)
admin.site.register(AccidentType)
admin.site.register(Company)
admin.site.register(Adjuster)
@admin.register(FactorScale)
class FactorScale(admin.ModelAdmin):
    list_display = ['factor', 'min', 'max']

@admin.register(Injuries)
class Injuries(admin.ModelAdmin):
    list_display = ['name', 'value']



