

from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('attorneyInfo/', views.attorneyInfo, name='attorneyInfo'),
    path('medicalProviders/', views.medicalProviders, name='medicalProviders'),
    path('marketer/', views.marketer, name='marketer'),
    path('marketerInfo/', views.marketerInfo, name='marketerInfo'),
    path('provider/<str:office_name>/', views.provider, name='provider'),
    path('privacy/', views.privacy, name='privacy'),
    path('contactus/', views.contactus, name='contactus'),
    path('createAccount/', views.createAccount, name='createAccount'),
    path('accounting/', views.accounting, name='accounting'),
    path('editAccounting/', views.editAccounting, name='editAccounting'),
    path('updateMarketerCode/', views.updateMarketerCode, name='updateMarketerCode'),
    path('requestUpdate/', views.requestUpdate, name='requestUpdate'),
    path('addRequestUpdate/<str:case_id>/', views.addRequestUpdate, name='addRequestUpdate'),
    path('case_add_attorney/', views.case_add_attorney, name='case_add_attorney'),
    path('addBPClient/', views.addBPClient, name='addBPClient'),
    path('upload/<str:client_id>/<str:case_id>/<str:doc_id>/', views.upload, name='upload'),
    path('TFUpload/<str:client_id>/<str:case_id>/<str:doc_id>/', views.TFUpload, name='TFUpload'),
    path('open_file/<str:doc_id>/', views.open_file, name='open_file'),

    path('attachAttorney/', views.attachAttorney, name='attachAttorney'),
    path('treating/', views.treating, name='treating'),
    path('treatmentDone/', views.treatmentDone, name='treatmentDone'),
    path('litigation/', views.litigation, name='litigation'),
    path('settlement/', views.settlement, name='settlement'),
    path('settled/', views.settled, name='settled'),
    path('paid/', views.paid, name='paid'),
    path('open/', views.openfilter, name='open'),
    path('close/', views.close, name='close'),
    path('newLead/', views.newLead, name='newLead'),

    path('accountingDetail/<str:case_id>/<str:tf_treatment_id>/', views.accountingDetail, name='accountingDetail'),

    #REST APIs
    path('case_management/', views.case_management, name='case_management'),
    path('getSpecialties/', views.AddPatientCaseManagement.as_view(), name='AddPatientCaseManagement'),
    path('ListPatientsCaseManagement/', views.ListPatientsCaseManagement.as_view(), name='ListPatientsCaseManagement'),
    path('FilterTFCaseStatus/', views.FilterTFCaseStatus.as_view(), name='FilterTFCaseStatus'),
    path('ClientAutoCompleteSearch/', views.ClientAutoCompleteSearch.as_view(), name='ClientAutoCompleteSearch'),
    path('AttorneyAutoCompleteSearch/', views.AttorneyAutoCompleteSearch.as_view(), name='AttorneyAutoCompleteSearch'),
    path('GetFirmUserCaseManagement/', views.GetFirmUserCaseManagement.as_view(), name='GetFirmUserCaseManagement'),
    path('AttachAttorneyCaseManagement/', views.AttachAttorneyCaseManagement.as_view(), name='AttachAttorneyCaseManagement'),
    path('ListLocations/', views.ListLocations.as_view(), name='ListLocations'),
    path('addBPCaseProvider/<str:client_id>/<str:case_id>/', views.addBPCaseProvider, name='addBPCaseProvider'),

    path('patientDetail/<str:client_id>/<str:case_id>/', views.patientDetail, name='patientDetail'),
    
    path('staff/users/locations', views.admin_dashboard, name='admin_dashboard'),
    path('staff/users/searchlocationbyoffice', views.admin_searchbyoffice, name='admin_searchbyoffice'),
    path('staff/users/searchlocationbyaddress', views.admin_searchbyaddress, name='admin_searchbyaddress'),
    path('staff/users/editprovider<str:provider_id>/', views.admin_editprovider, name='admin_editprovider'),
    path('staff/users/importproviders/', views.admin_importproviders, name='admin_importproviders'),
    path('staff/users/addProviderIndividual/', views.addProviderIndividual, name='addProviderIndividual'),

    path('multipleusers/', views.multipleusers, name='multipleusers'),
    path('editmultipleuser/<str:user_id>/', views.editmultipleuser, name='editmultipleuser'),
    path('deletemultipleuser/<str:user_id>/', views.deletemultipleuser, name='deletemultipleuser'),

    path('addlocations/', views.addlocations, name='addlocations'),
    path('adddoctors/', views.adddoctors, name='adddoctors'),
    path('editlocations/<str:location_id>/<str:provider_id>/', views.editlocations, name='editlocations'),
    path('profile/', views.profile, name='profile'),

    path('accountdetails/', views.accountdetails, name='accountdetails'),
    path('providerdetails/', views.providerdetails, name='providerdetails'),
    path('accountdetails_attorney/', views.accountdetails_attorney, name='accountdetails_attorney'),
    path('accountdetails_marketer/', views.accountdetails_marketer, name='accountdetails_marketer'),
    path('attorneylocation/', views.attorneylocation, name='attorneylocation'),
    path('marketerlocation/', views.marketerlocation, name='marketerlocation'),
    

    path('attorney_profile/', views.attorney_profile, name='attorney_profile'),
    path('firm_users/', views.firm_users, name='firm_users'),
    path('provider_firm_users/', views.provider_firm_users, name='provider_firm_users'),
    path('blacklist/', views.blacklist, name='blacklist'),
    path('flagged_users/', views.flagged_users, name='flagged_users'),
    path('provider_reviews/', views.provider_reviews, name='provider_reviews'),
    path('marketer_code/<str:attorney_id>/', views.marketer_code, name='marketer_code'),

    path('marketer_profile/', views.marketer_profile, name='marketer_profile'),
    path('marketer_firm_users/', views.marketer_firm_users, name='marketer_firm_users'),
    path('marketer_blacklist/', views.marketer_blacklist, name='marketer_blacklist'),
    path('marketer/', views.marketer, name='marketer'),
    path('marketer_provider_reviews/', views.marketer_provider_reviews, name='marketer_provider_reviews'),

    path('addFavorite/<str:provider_id>/<str:location_id>/<str:specialty_id>/', views.addFavorite, name='addFavorite'),
    path('removeFavorite/<str:favorite_id>/', views.removeFavorite, name='removeFavorite'),
    path('addBlacklist/<str:provider_id>/', views.addBlacklist, name='addBlacklist'),
    path('addFlagged/<str:provider_id>/', views.addFlagged, name='addFlagged'),
    path('favorites/', views.favorites, name='favorites'),

    path('addNewFirm/<str:client_id>/<str:case_id>/', views.addNewFirm, name='addNewFirm'),
    path('addTFNotes/<str:client_id>/<str:case_id>/', views.addTFNotes, name='addTFNotes'),
    path('addTFToDo/<str:client_id>/<str:case_id>/', views.addTFToDo, name='addTFToDo'),


    path('filters/', views.filters, name='filters'),
    path('reports/', views.reports, name='reports'),
    path('generateReport/', views.generateReport, name='generateReport'),
    path('addTFTreatmentDates/', views.addTFTreatmentDates, name='addTFTreatmentDates'),
    path('TFTodo/', views.TFTodo, name='TFTodo'),
    path('todoCompleted/', views.todoCompleted, name='todoCompleted'),
    path('advance_filters/', views.advance_filters, name='advance_filters'),

    path('register/<str:role>/', views.register, name='register'),
    path('loginPage/', views.loginPage, name='loginPage'),
    path('logoutPage/', views.logoutPage, name='logoutPage'),


    path('reset_password/', auth_views.PasswordResetView.as_view(), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
