

from cmath import acos
import datetime
from email import message

from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib import messages
import random, string
from accounts.models import Attorney, AttorneyLocation, AttorneyStaff, Doctor, Favorite, Flagged, Marketer, MarketerLocation, MarketerStaff, OtherLocations, Provider, Location, ProviderStaff, Review, Specialty, Firm, TFAccounting, TFCaseStatus, TFDoc, TFTreatmentDate
from django.conf import settings

import googlemaps
from math import cos, asin, sqrt, pi
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
import csv

from BP.models import BPAccounting, Firm as BPFirm, Attorney as BPAttorney, AttorneyLocation as BPAttorneyLocation, Client as BPClient, Case as BPCase, CaseProviders as BPCaseProviders, Doc as BPDoc, ClientStatus as BPClientStatus, AttorneyStaff as BPAttorneyStaff, ClientStatus as BPClientStatus, AttorneyUserType as BPAttorneyUserType, CaseType as BPCaseType, TFNotes, TFTodos, RequestUpdate, ToDo as BPToDo
from BP.serializers import AttorneySerializer, AttorneyStaffSerializer, ClientSerializer, DocSerializer
import os
from django.http import JsonResponse, StreamingHttpResponse
from wsgiref.util import FileWrapper, request_uri
from django.views.decorators.clickjacking import xframe_options_sameorigin
import mimetypes

from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView
from accounts.serializers import LocationSerializer, SpecialtySerializer, TFDocSerializer
from rest_framework.response import Response
from datetime import datetime 
import datetime as dt



def requestUpdate(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    provider_cases = []
    case_providers = BPCaseProviders.objects.filter(provider=userprofile)
    for case_provider in case_providers:
        case = BPCase.objects.get(pk=case_provider.for_case.id)
        check = False
        temp_check = False
        for x in provider_cases:
            if x['id'] == case.id:
                check = True
                break
        if not check:
            request_update = RequestUpdate.objects.get(for_case=case)
            current_date = str(datetime.today().strftime('%m-%d-%Y'))
            date_format = '%m-%d-%Y'
            a = datetime.strptime(current_date, date_format)
            b = datetime.strptime(request_update.status_changed_on, date_format)
            delta = a - b
            print(delta.days)
            temp_delta = 0
            if request_update.isRequested:
                bb = datetime.strptime(request_update.requested_at, date_format)
                temp_delta = a - bb
            if (delta.days > 90 and case.case_status.name != 'New Lead'):
                
                firm_user = case.firm_users.all()
                temp_check = True
                if request_update.isRequested:
                    if temp_delta.days > 30:
                        temp_check = True
                        request_update.isRequested = False
                        request_update.save()
                    else:
                        temp_check = False
                firm_user_name = '-'
                firm_user_extension = '-'
                
                if firm_user:
                    firm_user = firm_user[0]
                    firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
                    
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                

                bp_attorney = case.for_client.created_by
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + ", " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    
                    'firm_user_name': firm_user_name,
                    'firm_user_extension': firm_user_extension,
                    'case_category':case.case_category,
                    # 'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name,
                    'recent_status':request_update.recent_status,
                    'status_date':request_update.status_changed_on,
                    'temp_check': temp_check,
                    'isRequested':request_update.isRequested,
                    'case_manager':request_update.changed_by,
                    'request_count':request_update.request_count

                })
              
    context = {
        'provider_cases':provider_cases
    }
    return render(request, 'accounts/requestUpdate.html', context)

def addRequestUpdate(request, case_id):
    bp_case = BPCase.objects.get(pk=int(case_id))
    current_date = dt.date.today()
    requested_on = str(current_date.strftime('%m-%d-%Y'))
    requestUpdate = RequestUpdate.objects.get(for_case=bp_case)
    requestUpdate.isRequested = True
    requestUpdate.requested_at = requested_on
    requestUpdate.request_count += 1
    requestUpdate.save()
    print('hello')
    
    print(current_date)
    firm_users = bp_case.firm_users.all()

    todo_for = None
    for firm_user in firm_users:
        if firm_user.user_type.name == 'case manager':
            todo_for = firm_user
    print(todo_for)
    bpTodo = BPToDo.objects.create(for_client=bp_case.for_client, for_case=bp_case, due_date=current_date, todo_for=todo_for, notes='Update Requested', todo_type='Update Requested')
    bpTodo.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addBPCaseProvider(request, client_id, case_id):
    if request.method == 'POST':
        #try:

            location_id = request.POST.get('location_id')
            specialty_id = request.POST.get('specialty_id')
            case_statuses = request.POST.get('case_statuses')
            first_visit = request.POST.get('first_visit')
            last_visit = request.POST.get('last_visit')
            visits = request.POST.get('visits')

            try:
                tf_case_status = TFCaseStatus.objects.get(pk=int(case_statuses))

            except:
                pass

            client = BPClient.objects.get(pk=int(client_id))
            case = BPCase.objects.get(pk=int(case_id))
            location = Location.objects.get(pk=int(location_id))
            specialty = Specialty.objects.get(pk=int(specialty_id))
            try:
                temp = BPCaseProviders.objects.get(for_case=case, location=location, provider=location.added_by, specialty=specialty)
                messages.error(request, 'Case Provider already Exists!')
                return redirect('patientDetail', int(client_id), int(case_id))
            except:
                pass
            client_provider = BPCaseProviders.objects.create(for_case=case, location=location, provider=location.added_by, specialty=specialty, tf_case_status=tf_case_status, first_date=first_visit, second_date=last_visit, visits=visits)
            client_provider.save()


            doc1 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 1', provider_documents=client_provider)
            doc1.save()
            doc2 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 2', provider_documents=client_provider)
            doc2.save()
            doc3 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 3', provider_documents=client_provider)
            doc3.save()
            doc4 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 4', provider_documents=client_provider)
            doc4.save()
            doc5 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 5', provider_documents=client_provider)
            doc5.save()
            doc6 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 6', provider_documents=client_provider)
            doc6.save()
            doc7 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='TF Bills', provider_documents=client_provider)
            doc7.save()
            doc8 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='TF Rec', provider_documents=client_provider)
            doc8.save()

            messages.success(request, 'Location & specialty has been attached successfully!')
        #except:
        #    messages.error(request, 'Operation Failed! Please try again.')
    return redirect('patientDetail', int(client_id), int(case_id))

class ListLocations(APIView):
    def get(self, request):
        try:
            profile = Firm.objects.get(user=request.user, account_type='Provider')
            userprofile = Provider.objects.get(providerprofile=profile)
        except:
            userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
            userprofile = userprofile.created_by

        locations = Location.objects.filter(added_by=userprofile)
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)


class AttachAttorneyCaseManagement(APIView):
    def get(self, request):

        attorney_id = self.request.query_params['attorney_id']
        firm_user_id = self.request.query_params['firm_user_id']
        client_id = self.request.query_params['client_id']
        case_id = self.request.query_params['case_id']
        bp_attorney = BPAttorney.objects.get(pk=int(attorney_id))
        if firm_user_id != '':
            bp_firm_user = BPAttorneyStaff.objects.get(pk=int(firm_user_id))
            bp_case.firm_users.add(bp_firm_user)
        bp_client = BPClient.objects.get(pk=int(client_id))
        bp_case = BPCase.objects.get(pk=int(case_id))
        bp_client.created_by = bp_attorney
        bp_client.save()
        
        bp_case.save()
        messages.success(request, 'Attorney and Firm User has been attached!')


        return Response({'message': 'done'})


class GetFirmUserCaseManagement(APIView):
    def get(self, request):
        attorney_id = self.request.query_params['attorney_id']
        bp_attorney = BPAttorney.objects.get(pk=int(attorney_id))
        firm_users = BPAttorneyStaff.objects.filter(created_by=bp_attorney)
        serializer = AttorneyStaffSerializer(firm_users, many=True)
        return Response(serializer.data)

class AttorneyAutoCompleteSearch(APIView):
    def get(self, request):
        attorney_name = self.request.query_params['attorney_name']
        bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=attorney_name))


        serializer = AttorneySerializer(bp_attorneys, many=True)
        return Response(serializer.data)

class ClientAutoCompleteSearch(APIView):
    def get(self, request):
        try:
            profile = Firm.objects.get(user=request.user, account_type='Provider')
            userprofile = Provider.objects.get(providerprofile=profile)

        except:
            userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
            userprofile = userprofile.created_by

        client_name = self.request.query_params['client_name']
        bp_clients = BPClient.objects.filter(Q(first_name__icontains=client_name)|Q(last_name__icontains=client_name))
        serializer = ClientSerializer(bp_clients, many=True)
        return Response(serializer.data)

class FilterTFCaseStatus(APIView):
    def get(self, request):
        try:
            profile = Firm.objects.get(user=request.user, account_type='Provider')
            userprofile = Provider.objects.get(providerprofile=profile)

        except:
            userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
            userprofile = userprofile.created_by
        
        temp_status_check = False
        tf_case_status = self.request.query_params['tf_case_status']
        open_close = self.request.query_params['open_close']
        isAccounting = 'False'
        try:
            isAccounting = self.request.query_params['accounting']
        except:
            pass
        print('this is tf_case_Status', tf_case_status)
        print('this is case status', open_close)
        if open_close != '':
            temp_status_check = True
        tf_case_status = tf_case_status.split(",")
        int_tf_case_status = []
        for x in tf_case_status:
            int_tf_case_status.append(int(x))
        print(int_tf_case_status)

        provider_cases = []
        # try:
        #     tf_case_status = TFCaseStatus.objects.get(pk=int(tf_case_status))
        # except:
        #     tf_case_status = None
        
        if len(tf_case_status) > 0:
            case_providers = None
            if not temp_status_check:
                case_providers = BPCaseProviders.objects.filter(provider=userprofile, tf_case_status__in=int_tf_case_status)
            else:
                if open_close == 'Close':
                    case_providers = BPCaseProviders.objects.filter(provider=userprofile, tf_case_status__in=int_tf_case_status, is_open=False)
                elif open_close == 'Open':
                    case_providers = BPCaseProviders.objects.filter(provider=userprofile, tf_case_status__in=int_tf_case_status, is_open=True)
            for case_provider in case_providers:
                
                case = BPCase.objects.get(pk=case_provider.for_case.id)
                temp_case_provider = BPCaseProviders.objects.filter(provider=userprofile,for_case=case)
                attached_specialties = []
                for x in temp_case_provider:
                    temp_spec = SpecialtySerializer(x.specialty, many=False)
                    attached_specialties.append(temp_spec.data)
                check = False
                if isAccounting == 'False':
                    for x in provider_cases:
                        if x['id'] == case.id:
                            check = True
                            break
                if not check:
                    tf_accounting = None
                    tf_accounting_id = None
                    try:
                        tf_accounting = TFAccounting.objects.get(created_by=userprofile, for_case_provider=case_provider)
                        tf_accounting_id = tf_accounting.id
                    except:
                        pass
                    print(tf_accounting)
                    tf_case_status = ''
                    if case_provider.is_open:
                        tf_case_status = 'Open'
                    else:
                        tf_case_status = 'Closed'
                    accounting_doc1 = None
                    accounting_doc2 = None
                    accounting_doc1_serializer = None
                    accounting_doc2_serializer = None
                    if tf_accounting:
                        accounting_doc1 = TFDoc.objects.get(document_no='Paid', for_provider=userprofile, for_tf_accounting=tf_accounting)
                        accounting_doc2 = TFDoc.objects.get(document_no='Cleared', for_provider=userprofile, for_tf_accounting=tf_accounting)
                        accounting_doc1_serializer = TFDocSerializer(accounting_doc1, many=False).data
                        accounting_doc2_serializer = TFDocSerializer(accounting_doc2, many=False).data
                    doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                    doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                    doc1_serializer = DocSerializer(doc1, many=False)
                    doc2_serializer = DocSerializer(doc2, many=False)
                    bp_attorney = case.for_client.created_by
                    attorney_location = BPAttorneyLocation.objects.filter(added_by=bp_attorney)

                    firm_user = case.firm_users.all()
                    loc = LocationSerializer(case_provider.location, many=False)
                    spec = SpecialtySerializer(case_provider.specialty, many=False)

                    attorney_phone_number = '-'
                    firm_user_name = '-'
                    firm_user_extension = '-'
                    if attorney_location:
                        attorney_location = attorney_location[0]
                        attorney_phone_number = attorney_location.phone
                    if firm_user:
                        firm_user = firm_user[0]
                        firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
                        firm_user_extension = firm_user.phone_extension
                    temp_office_name = ''
                    if case.for_client.created_by:
                        temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                    else:
                        temp_office_name = '-'
                    total = 0
                    check_number = ''
                    if tf_accounting:
                        check_number = tf_accounting.check_number
                    
                    payments = '{:.2f}'.format(0)
                    reductions = '{:.2f}'.format(0)
                    liens = '{:.2f}'.format(0)
                    
                    
                    hi_paid = tf_accounting.hi_paid
                    hi_reduction = tf_accounting.hi_reduction
                    original = '{:.2f}'.format(tf_accounting.original)
                    reduction = tf_accounting.reduction
                    patient_payment_value = tf_accounting.patient_payment_value
                    check_number = tf_accounting.check_number
                    mp_paid = tf_accounting.mp_paid
                    total = '{:.2f}'.format(tf_accounting.final)
                    liens = '{:.2f}'.format(tf_accounting.liens)
                    payments = '{:.2f}'.format(tf_accounting.payments)
                    reductions = '{:.2f}'.format(tf_accounting.reductions)
                    payment_received_date = tf_accounting.payment_received_date
                        
                    # if tf_accounting and tf_accounting.patient_payment_value:
                    #     patient_payment_value = '{:.2f}'.format(tf_accounting.patient_payment_value)
                    #     total += float(patient_payment_value)
                    #     payments += float(patient_payment_value)
                    #     liens += float(patient_payment_value)
                    # if tf_accounting and tf_accounting.hi_reduction:
                    #     hi_reduction = '{:.2f}'.format(tf_accounting.hi_reduction)
                        
                    #     reductions += float(hi_reduction)
                    #     liens += float(hi_reduction)
                    # if tf_accounting and tf_accounting.mp_paid:
                    #     mp_paid = '{:.2f}'.format(tf_accounting.mp_paid)
                    #     total += float(mp_paid)
                    #     payments += float(mp_paid)
                    #     liens += float(mp_paid)
                    # if tf_accounting and tf_accounting.reduction:
                    #     reduction = '{:.2f}'.format(tf_accounting.reduction)
                        
                    #     reductions += float(reduction)
                    #     liens += float(reduction)
                    # if tf_accounting and tf_accounting.original:
                    #     original = '{:.2f}'.format(tf_accounting.original)
                        
                    #     liens = float(float(original) - liens)
                    #     total = float(float(total) + liens)
                        
                    # else:
                    #     total = '{:.2f}'.format(0)
                    provider_cases.append({
                        'id':case.id,
                        'client_id':case.for_client.id,
                        'client_name': case.for_client.last_name + ", " + case.for_client.first_name,
                        'birthday': case.for_client.birthday,
                        'incident_date':case.incident_date,
                        'case_type':case.case_type.name,
                        'case_provider':case_provider.id,
                        'doc_1':doc1_serializer.data,
                        'doc_2':doc2_serializer.data,
                        'accounting_doc_1': accounting_doc1_serializer,
                        'accounting_doc_2':accounting_doc2_serializer,
                        'address': loc.data,
                        'specialty': spec.data,
                        'attorney_phone_number': attorney_phone_number,
                        'firm_user_name': firm_user_name,
                        'firm_user_extension': firm_user_extension,
                        'case_category':case.case_category,
                        # 'case_status':case.case_status,
                        'check_number': check_number,
                        'date_closed':case.date_closed,
                        "office_name":temp_office_name,
                        'status':tf_case_status,
                        'original': original,
                        'hi_paid': hi_paid,
                        'hi_reduction':hi_reduction,
                        'mp_paid':hi_paid,
                        'reduction':reduction,
                        'patient_payment_value': patient_payment_value,
                        'payments':payments,
                        'liens': liens,
                        'reductions': reductions,
                        'final':total,
                        'payment_received_date':payment_received_date,
                        'attached_specialties':attached_specialties,
                        'tf_accounting_id':tf_accounting_id,
                    })
        context = {
            'response': provider_cases
        }
        return Response(context)

class ListPatientsCaseManagement(APIView):
    def get(self, request):
        try:
            profile = Firm.objects.get(user=request.user, account_type='Provider')
            userprofile = Provider.objects.get(providerprofile=profile)

        except:
            userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
            userprofile = userprofile.created_by

        provider_cases = []

        # locations = Location.objects.filter(added_by=userprofile)
        # client_statuses = BPClientStatus.objects.all()

        bp_attorneys = None
        # temp_attorneys = BPAttorney.objects.all()
        attorney_id = self.request.query_params['attorney_id']
        client_id = self.request.query_params['client_id']
        isAccounting = 'False'
        try:
            isAccounting = self.request.query_params['accounting']
        except:
            pass

        # search_clients = self.request.query_params['client_name']


        if client_id == '' and attorney_id == '':
            case_providers = BPCaseProviders.objects.filter(provider=userprofile)
            for case_provider in case_providers:
                case = BPCase.objects.get(pk=case_provider.for_case.id)
                
                temp_case_provider = BPCaseProviders.objects.filter(provider=userprofile,for_case=case)
                attached_specialties = []
                for x in temp_case_provider:
                    temp_spec = SpecialtySerializer(x.specialty, many=False)
                    attached_specialties.append(temp_spec.data)
                check = False
                if isAccounting == 'False':
                    for x in provider_cases:
                        if x['id'] == case.id:
                            check = True
                            break
                if not check:
                    tf_accounting = None
                    tf_accounting_id = None
                    try:
                        tf_accounting = TFAccounting.objects.get(created_by=userprofile, for_case_provider=case_provider)
                        tf_accounting_id = tf_accounting.id
                    except:
                        pass
                    print(tf_accounting)
                    tf_case_status = ''
                    if case_provider.is_open:
                        tf_case_status = 'Open'
                    else:
                        tf_case_status = 'Closed'
                    accounting_doc1 = None
                    accounting_doc2 = None
                    accounting_doc1_serializer = None
                    accounting_doc2_serializer = None
                    if tf_accounting:
                        accounting_doc1 = TFDoc.objects.get(document_no='Paid', for_provider=userprofile, for_tf_accounting=tf_accounting)
                        accounting_doc2 = TFDoc.objects.get(document_no='Cleared', for_provider=userprofile, for_tf_accounting=tf_accounting)
                        accounting_doc1_serializer = TFDocSerializer(accounting_doc1, many=False).data
                        accounting_doc2_serializer = TFDocSerializer(accounting_doc2, many=False).data
                    doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                    doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                    doc1_serializer = DocSerializer(doc1, many=False)
                    doc2_serializer = DocSerializer(doc2, many=False)
                    bp_attorney = case.for_client.created_by
                    attorney_location = BPAttorneyLocation.objects.filter(added_by=bp_attorney)

                    firm_user = case.firm_users.all()
                    loc = LocationSerializer(case_provider.location, many=False)
                    spec = SpecialtySerializer(case_provider.specialty, many=False)

                    attorney_phone_number = '-'
                    firm_user_name = '-'
                    firm_user_extension = '-'
                    if attorney_location:
                        attorney_location = attorney_location[0]
                        attorney_phone_number = attorney_location.phone
                    if firm_user:
                        firm_user = firm_user[0]
                        firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
                        firm_user_extension = firm_user.phone_extension
                    temp_office_name = ''
                    if case.for_client.created_by:
                        temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                    else:
                        temp_office_name = '-'
                    total = 0
                    check_number = ''
                    if tf_accounting:
                        check_number = tf_accounting.check_number
                    
                    payments = '{:.2f}'.format(0)
                    reductions = '{:.2f}'.format(0)
                    liens = '{:.2f}'.format(0)
                    
                    
                    hi_paid = tf_accounting.hi_paid
                    hi_reduction = tf_accounting.hi_reduction
                    original = '{:.2f}'.format(tf_accounting.original)
                    reduction = tf_accounting.reduction
                    patient_payment_value = tf_accounting.patient_payment_value
                    check_number = tf_accounting.check_number
                    mp_paid = tf_accounting.mp_paid
                    total = '{:.2f}'.format(tf_accounting.final)
                    liens = '{:.2f}'.format(tf_accounting.liens)
                    payments = '{:.2f}'.format(tf_accounting.payments)
                    reductions = '{:.2f}'.format(tf_accounting.reductions)
                    payment_received_date = tf_accounting.payment_received_date
                        
                    # if tf_accounting and tf_accounting.patient_payment_value:
                    #     patient_payment_value = '{:.2f}'.format(tf_accounting.patient_payment_value)
                    #     total += float(patient_payment_value)
                    #     payments += float(patient_payment_value)
                    #     liens += float(patient_payment_value)
                    # if tf_accounting and tf_accounting.hi_reduction:
                    #     hi_reduction = '{:.2f}'.format(tf_accounting.hi_reduction)
                        
                    #     reductions += float(hi_reduction)
                    #     liens += float(hi_reduction)
                    # if tf_accounting and tf_accounting.mp_paid:
                    #     mp_paid = '{:.2f}'.format(tf_accounting.mp_paid)
                    #     total += float(mp_paid)
                    #     payments += float(mp_paid)
                    #     liens += float(mp_paid)
                    # if tf_accounting and tf_accounting.reduction:
                    #     reduction = '{:.2f}'.format(tf_accounting.reduction)
                        
                    #     reductions += float(reduction)
                    #     liens += float(reduction)
                    # if tf_accounting and tf_accounting.original:
                    #     original = '{:.2f}'.format(tf_accounting.original)
                        
                    #     liens = float(float(original) - liens)
                    #     total = float(float(total) + liens)
                        
                    # else:
                    #     total = '{:.2f}'.format(0)
                    provider_cases.append({
                        'id':case.id,
                        'client_id':case.for_client.id,
                        'client_name': case.for_client.last_name + ", " + case.for_client.first_name,
                        'birthday': case.for_client.birthday,
                        'incident_date':case.incident_date,
                        'case_type':case.case_type.name,
                        'case_provider':case_provider.id,
                        'doc_1':doc1_serializer.data,
                        'doc_2':doc2_serializer.data,
                        'accounting_doc_1': accounting_doc1_serializer,
                        'accounting_doc_2':accounting_doc2_serializer,
                        'address': loc.data,
                        'specialty': spec.data,
                        'attorney_phone_number': attorney_phone_number,
                        'firm_user_name': firm_user_name,
                        'firm_user_extension': firm_user_extension,
                        'case_category':case.case_category,
                        # 'case_status':case.case_status,
                        'check_number': check_number,
                        'date_closed':case.date_closed,
                        "office_name":temp_office_name,
                        'status':tf_case_status,
                        'original': original,
                        'hi_paid': hi_paid,
                        'hi_reduction':hi_reduction,
                        'mp_paid':hi_paid,
                        'reduction':reduction,
                        'patient_payment_value': patient_payment_value,
                        'payments':payments,
                        'liens': liens,
                        'reductions': reductions,
                        'final':total,
                        'payment_received_date':payment_received_date,
                        'attached_specialties':attached_specialties,
                        'tf_accounting_id':tf_accounting_id,
                    })

        elif client_id == '':
            bp_attorney = BPAttorney.objects.get(pk=int(attorney_id))
            temp_clients = []

            clients = BPClient.objects.filter(created_by=bp_attorney)
            for client in clients:
                cases = BPCase.objects.filter(for_client=client)

                for case in cases:
                    case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                    
                    
                    print('cases & case_providers', case, case_providers)
                    for case_provider in case_providers:
                        case = BPCase.objects.get(pk=case_provider.for_case.id)
                        temp_case_provider = BPCaseProviders.objects.filter(provider=userprofile,for_case=case)
                        attached_specialties = []
                        for x in temp_case_provider:
                            temp_spec = SpecialtySerializer(x.specialty, many=False)
                            attached_specialties.append(temp_spec.data)
                        check = False
                        if isAccounting == 'False':
                            for x in provider_cases:
                                if x['id'] == case.id:
                                    check = True
                                    break
                        if not check:
                            tf_accounting = None
                            tf_accounting_id = None
                            try:
                                tf_accounting = TFAccounting.objects.get(created_by=userprofile, for_case_provider=case_provider)
                                tf_accounting_id = tf_accounting.id
                            except:
                                pass
                            print(tf_accounting)
                            tf_case_status = ''
                            if case_provider.is_open:
                                tf_case_status = 'Open'
                            else:
                                tf_case_status = 'Closed'
                            accounting_doc1 = None
                            accounting_doc2 = None
                            accounting_doc1_serializer = None
                            accounting_doc2_serializer = None
                            if tf_accounting:
                                accounting_doc1 = TFDoc.objects.get(document_no='Paid', for_provider=userprofile, for_tf_accounting=tf_accounting)
                                accounting_doc2 = TFDoc.objects.get(document_no='Cleared', for_provider=userprofile, for_tf_accounting=tf_accounting)
                                accounting_doc1_serializer = TFDocSerializer(accounting_doc1, many=False).data
                                accounting_doc2_serializer = TFDocSerializer(accounting_doc2, many=False).data
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            doc1_serializer = DocSerializer(doc1, many=False)
                            doc2_serializer = DocSerializer(doc2, many=False)
                            bp_attorney = case.for_client.created_by
                            attorney_location = BPAttorneyLocation.objects.filter(added_by=bp_attorney)

                            firm_user = case.firm_users.all()
                            loc = LocationSerializer(case_provider.location, many=False)
                            spec = SpecialtySerializer(case_provider.specialty, many=False)

                            attorney_phone_number = '-'
                            firm_user_name = '-'
                            firm_user_extension = '-'
                            if attorney_location:
                                attorney_location = attorney_location[0]
                                attorney_phone_number = attorney_location.phone
                            if firm_user:
                                firm_user = firm_user[0]
                                firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
                                firm_user_extension = firm_user.phone_extension
                            temp_office_name = ''
                            if case.for_client.created_by:
                                temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                            else:
                                temp_office_name = '-'
                            total = 0
                            check_number = ''
                            
                            if tf_accounting:
                                check_number = tf_accounting.check_number
                            
                            payments = '{:.2f}'.format(0)
                            reductions = '{:.2f}'.format(0)
                            liens = '{:.2f}'.format(0)
                            
                            
                            hi_paid = tf_accounting.hi_paid
                            hi_reduction = tf_accounting.hi_reduction
                            original = '{:.2f}'.format(tf_accounting.original)
                            reduction = tf_accounting.reduction
                            patient_payment_value = tf_accounting.patient_payment_value
                            check_number = tf_accounting.check_number
                            mp_paid = tf_accounting.mp_paid
                            total = '{:.2f}'.format(tf_accounting.final)
                            liens = '{:.2f}'.format(tf_accounting.liens)
                            payments = '{:.2f}'.format(tf_accounting.payments)
                            reductions = '{:.2f}'.format(tf_accounting.reductions)
                            payment_received_date = tf_accounting.payment_received_date
                                
                            # if tf_accounting and tf_accounting.patient_payment_value:
                            #     patient_payment_value = '{:.2f}'.format(tf_accounting.patient_payment_value)
                            #     total += float(patient_payment_value)
                            #     payments += float(patient_payment_value)
                            #     liens += float(patient_payment_value)
                            # if tf_accounting and tf_accounting.hi_reduction:
                            #     hi_reduction = '{:.2f}'.format(tf_accounting.hi_reduction)
                                
                            #     reductions += float(hi_reduction)
                            #     liens += float(hi_reduction)
                            # if tf_accounting and tf_accounting.mp_paid:
                            #     mp_paid = '{:.2f}'.format(tf_accounting.mp_paid)
                            #     total += float(mp_paid)
                            #     payments += float(mp_paid)
                            #     liens += float(mp_paid)
                            # if tf_accounting and tf_accounting.reduction:
                            #     reduction = '{:.2f}'.format(tf_accounting.reduction)
                                
                            #     reductions += float(reduction)
                            #     liens += float(reduction)
                            # if tf_accounting and tf_accounting.original:
                            #     original = '{:.2f}'.format(tf_accounting.original)
                                
                            #     liens = float(float(original) - liens)
                            #     total = float(float(total) + liens)
                                
                            # else:
                            #     total = '{:.2f}'.format(0)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + ", " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'case_provider':case_provider.id,
                                'doc_1':doc1_serializer.data,
                                'doc_2':doc2_serializer.data,
                                'accounting_doc_1': accounting_doc1_serializer,
                                'accounting_doc_2':accounting_doc2_serializer,
                                'address': loc.data,
                                'specialty': spec.data,
                                'attorney_phone_number': attorney_phone_number,
                                'firm_user_name': firm_user_name,
                                'firm_user_extension': firm_user_extension,
                                'case_category':case.case_category,
                                # 'case_status':case.case_status,
                                'check_number': check_number,
                                'date_closed':case.date_closed,
                                "office_name":temp_office_name,
                                'status':tf_case_status,
                                'original': original,
                                'hi_paid': hi_paid,
                                'hi_reduction':hi_reduction,
                                'mp_paid':hi_paid,
                                'reduction':reduction,
                                'patient_payment_value': patient_payment_value,
                                'payments':payments,
                                'liens': liens,
                                'reductions': reductions,
                                'final':total,
                                'payment_received_date':payment_received_date,
                                'attached_specialties':attached_specialties,
                                'tf_accounting_id':tf_accounting_id,
                            })

        elif attorney_id == '':
            bp_client = BPClient.objects.get(pk=int(client_id))
            cases = BPCase.objects.filter(for_client=bp_client)

            for case in cases:
                case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                print('cases & case_providers', case, case_providers)
                
                
                for case_provider in case_providers:
                    case = BPCase.objects.get(pk=case_provider.for_case.id)
                    temp_case_provider = BPCaseProviders.objects.filter(provider=userprofile,for_case=case)
                    attached_specialties = []
                    for x in temp_case_provider:
                        temp_spec = SpecialtySerializer(x.specialty, many=False)
                        attached_specialties.append(temp_spec.data)
                    check = False
                    if isAccounting == 'False':
                        for x in provider_cases:
                            if x['id'] == case.id:
                                check = True
                                break
                    if not check:
                        tf_accounting = None
                        tf_accounting_id = None
                        try:
                            tf_accounting = TFAccounting.objects.get(created_by=userprofile, for_case_provider=case_provider)
                            tf_accounting_id = tf_accounting.id
                        except:
                            pass
                        print(tf_accounting)
                        tf_case_status = ''
                        if case_provider.is_open:
                            tf_case_status = 'Open'
                        else:
                            tf_case_status = 'Closed'
                        accounting_doc1 = None
                        accounting_doc2 = None
                        accounting_doc1_serializer = None
                        accounting_doc2_serializer = None
                        if tf_accounting:
                            accounting_doc1 = TFDoc.objects.get(document_no='Paid', for_provider=userprofile, for_tf_accounting=tf_accounting)
                            accounting_doc2 = TFDoc.objects.get(document_no='Cleared', for_provider=userprofile, for_tf_accounting=tf_accounting)
                            accounting_doc1_serializer = TFDocSerializer(accounting_doc1, many=False).data
                            accounting_doc2_serializer = TFDocSerializer(accounting_doc2, many=False).data
                        doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                        doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                        doc1_serializer = DocSerializer(doc1, many=False)
                        doc2_serializer = DocSerializer(doc2, many=False)
                        bp_attorney = case.for_client.created_by
                        attorney_location = BPAttorneyLocation.objects.filter(added_by=bp_attorney)

                        firm_user = case.firm_users.all()
                        loc = LocationSerializer(case_provider.location, many=False)
                        spec = SpecialtySerializer(case_provider.specialty, many=False)

                        attorney_phone_number = '-'
                        firm_user_name = '-'
                        firm_user_extension = '-'
                        if attorney_location:
                            attorney_location = attorney_location[0]
                            attorney_phone_number = attorney_location.phone
                        if firm_user:
                            firm_user = firm_user[0]
                            firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
                            firm_user_extension = firm_user.phone_extension
                        temp_office_name = ''
                        if case.for_client.created_by:
                            temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                        else:
                            temp_office_name = '-'
                        total = 0
                        check_number = ''
                        if tf_accounting:
                            check_number = tf_accounting.check_number
                        
                        payments = '{:.2f}'.format(0)
                        reductions = '{:.2f}'.format(0)
                        liens = '{:.2f}'.format(0)
                        
                        
                        hi_paid = tf_accounting.hi_paid
                        hi_reduction = tf_accounting.hi_reduction
                        original = '{:.2f}'.format(tf_accounting.original)
                        reduction = tf_accounting.reduction
                        patient_payment_value = tf_accounting.patient_payment_value
                        check_number = tf_accounting.check_number
                        mp_paid = tf_accounting.mp_paid
                        total = '{:.2f}'.format(tf_accounting.final)
                        liens = '{:.2f}'.format(tf_accounting.liens)
                        payments = '{:.2f}'.format(tf_accounting.payments)
                        reductions = '{:.2f}'.format(tf_accounting.reductions)
                        payment_received_date = tf_accounting.payment_received_date
                            
                        # if tf_accounting and tf_accounting.patient_payment_value:
                        #     patient_payment_value = '{:.2f}'.format(tf_accounting.patient_payment_value)
                        #     total += float(patient_payment_value)
                        #     payments += float(patient_payment_value)
                        #     liens += float(patient_payment_value)
                        # if tf_accounting and tf_accounting.hi_reduction:
                        #     hi_reduction = '{:.2f}'.format(tf_accounting.hi_reduction)
                            
                        #     reductions += float(hi_reduction)
                        #     liens += float(hi_reduction)
                        # if tf_accounting and tf_accounting.mp_paid:
                        #     mp_paid = '{:.2f}'.format(tf_accounting.mp_paid)
                        #     total += float(mp_paid)
                        #     payments += float(mp_paid)
                        #     liens += float(mp_paid)
                        # if tf_accounting and tf_accounting.reduction:
                        #     reduction = '{:.2f}'.format(tf_accounting.reduction)
                            
                        #     reductions += float(reduction)
                        #     liens += float(reduction)
                        # if tf_accounting and tf_accounting.original:
                        #     original = '{:.2f}'.format(tf_accounting.original)
                            
                        #     liens = float(float(original) - liens)
                        #     total = float(float(total) + liens)
                            
                        # else:
                        #     total = '{:.2f}'.format(0)
                        provider_cases.append({
                            'id':case.id,
                            'client_id':case.for_client.id,
                            'client_name': case.for_client.last_name + ", " + case.for_client.first_name,
                            'birthday': case.for_client.birthday,
                            'incident_date':case.incident_date,
                            'case_type':case.case_type.name,
                            'case_provider':case_provider.id,
                            'doc_1':doc1_serializer.data,
                            'doc_2':doc2_serializer.data,
                            'accounting_doc_1': accounting_doc1_serializer,
                            'accounting_doc_2':accounting_doc2_serializer,
                            'address': loc.data,
                            'specialty': spec.data,
                            'attorney_phone_number': attorney_phone_number,
                            'firm_user_name': firm_user_name,
                            'firm_user_extension': firm_user_extension,
                            'case_category':case.case_category,
                            # 'case_status':case.case_status,
                            'check_number': check_number,
                            'date_closed':case.date_closed,
                            "office_name":temp_office_name,
                            'status':tf_case_status,
                            'original': original,
                            'hi_paid': hi_paid,
                            'hi_reduction':hi_reduction,
                            'mp_paid':hi_paid,
                            'reduction':reduction,
                            'patient_payment_value': patient_payment_value,
                            'payments':payments,
                            'liens': liens,
                            'reductions': reductions,
                            'final':total,
                            'payment_received_date':payment_received_date,
                            'attached_specialties':attached_specialties,
                            'tf_accounting_id':tf_accounting_id,
                        })

        print(provider_cases)
        context = {
                'response': provider_cases
            }
        return Response(context)


class AddPatientCaseManagement(ListCreateAPIView):
    def get_queryset(self):
        location_id = self.request.query_params.get('location_id')
        location = Location.objects.get(pk=int(location_id))
        queryset = location.specialties.all()
        return queryset
    serializer_class = SpecialtySerializer

def todoCompleted(request):
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
    if request.method == "POST":
        note = request.POST.get('note')
        todo_id = request.POST.get('todo_id')
        todo_id = int(todo_id)
        todo = TFTodos.objects.get(pk=todo_id)
        todo.completed_note = note
        todo.status = 'Completed'
        current_date = dt.date.today()
        todo.completed_at = current_date
        todo.save()

        notes = TFNotes.objects.create(created_by=request.user, for_case=todo.for_case, for_provider=userprofile, description=todo.completed_note, category='To-Do')
        notes.save()
    return redirect('TFTodo')

def TFTodo(request):
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        
    todos = None
    todos = TFTodos.objects.filter(todo_for=request.user)
    
    context = {
        'todos': todos, 
    }
    return render(request, 'accounts/TFTodos.html', context)

def addTFToDo(request, client_id, case_id):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by  
    bp_client = BPClient.objects.get(pk=client_id)
    bp_case = BPCase.objects.get(pk=case_id)
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        due_date = request.POST.get('due_date')
        description = request.POST.get('description')
        
        providerstaff_user = User.objects.get(pk=int(user_type))
        current_date = dt.date.today()
        
    
        if due_date == '1 day':
            current_date = current_date + dt.timedelta(days=1)
        elif due_date == '2 days':
            current_date = current_date + dt.timedelta(days=2)
        elif due_date == '3 days':
            current_date = current_date + dt.timedelta(days=3)
        elif due_date == '4 days':
            current_date = current_date + dt.timedelta(days=4)
        elif due_date == '5 days':
            current_date = current_date + dt.timedelta(days=5)
        elif due_date == '6 days':
            current_date = current_date + dt.timedelta(days=6)
        elif due_date == '1 week':
            current_date = current_date + dt.timedelta(days=7)
        elif due_date == '2 weeks':
            current_date = current_date + dt.timedelta(days=14)
        elif due_date == '1 month':
            current_date = current_date + dt.timedelta(days=30)
        elif due_date == '2 months':
            current_date = current_date + dt.timedelta(days=60)
        elif due_date == '6 months':
            current_date = current_date + dt.timedelta(days=180)

        todo = TFTodos.objects.create(created_by=request.user, for_case=bp_case, due_date=current_date, todo_for=providerstaff_user, notes=description)
        todo.save()
        description = 'To-Do for '+ providerstaff_user.first_name + ' due in ' + str(current_date) + ': ' + description 
        notes = TFNotes.objects.create(created_by=request.user, for_case=bp_case, for_provider=userprofile, description=description, category='To-Do')
        notes.save()
    return redirect('patientDetail', bp_client.id, bp_case.id)


def addTFNotes(request, client_id, case_id):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by  
    bp_client = BPClient.objects.get(pk=client_id)
    bp_case = BPCase.objects.get(pk=case_id)
    if request.method == 'POST':
        description = request.POST.get('note_description')
        print('this is description', description)
        category = request.POST.get('category')

        note = TFNotes.objects.create(for_provider=userprofile, created_by=request.user, for_case=bp_case, description=description, category=category)
        note.save()
    return redirect('patientDetail', bp_client.id, bp_case.id)

def addTFTreatmentDates(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    treatmentDate = None
    if request.method == 'POST':
        first_date = request.POST.get('first_date')
        
        second_date = request.POST.get('second_date')
        treatmentDate = request.POST.get('treatmentDate')
        tf_case_status = request.POST.get('tf_case_status')
        tf_stage = request.POST.get('tf_stage')

        name = request.POST.get('name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        phone = request.POST.get('phone')

        fax = request.POST.get('fax')

        print(tf_stage)
        print(treatmentDate)
        if first_date == '':
            first_date = '_/_/_'
        if second_date == '':
            second_date = '_/_/_'
        case_provider_id = request.POST.get('case_provider_id')
        case_id = request.POST.get('case_id')
        
        visits = request.POST.get('visits')
        case_provider = BPCaseProviders.objects.get(pk=int(case_provider_id))
        case_provider.provider.providerprofile.office_name = name
        case_provider.location.address = address
        case_provider.location.address2 = address2
        case_provider.location.city = city
        case_provider.location.state = state
        case_provider.location.phone = phone
        case_provider.location.email = email
        case_provider.location.fax = fax
        case_provider.location.save()
        case_provider.provider.save()
        case = BPCase.objects.get(pk=int(case_id))
        
        try:
            tf_case_status = TFCaseStatus.objects.get(pk=int(tf_case_status))
            case_provider.tf_case_status = tf_case_status
            case_provider.save()
        except:
            pass

        if tf_stage == 'open':
            case_provider.is_open = True
            
        else:
            case_provider.is_open = False
        case_provider.save()
            
        
        if visits != '':
            visits = int(visits)
        else:
            visits = '__'
        try:
            treatmentDate = TFTreatmentDate.objects.get(pk=int(treatmentDate))
            print()
            treatmentDate.first_date = first_date
            treatmentDate.second_date = second_date
            treatmentDate.visits = visits


        except:
            treatmentDate = TFTreatmentDate.objects.create(created_by=userprofile, first_date=first_date, second_date=second_date, visits=visits, for_case_provider=case_provider, for_case=case)
        
           
        treatmentDate.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def accountingDetail(request, case_id, tf_treatment_id):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    
    
    bp_case = BPCase.objects.get(pk=case_id)
    client = bp_case.for_client
    tf_accounting = TFAccounting.objects.get(pk=tf_treatment_id)
    accounting_doc_1 = TFDoc.objects.get(for_tf_accounting=tf_accounting, document_no='Paid')
    accounting_doc_2 = TFDoc.objects.get(for_tf_accounting=tf_accounting, document_no='Cleared')
    tf_case_status = TFCaseStatus.objects.all()
    case_providers = BPCaseProviders.objects.filter(for_case=bp_case,  provider=userprofile)
    locations = Location.objects.filter(added_by=userprofile)
    case_statuses = BPClientStatus.objects.all()
    user_types = BPAttorneyUserType.objects.all()
    tf_notes = TFNotes.objects.filter(for_case=bp_case)
    provider_users = ProviderStaff.objects.filter(created_by=userprofile)
    print(provider_users)
    temp_providers=[]
    for case_provider in case_providers:
        try:
            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=bp_case, provider_documents=case_provider)
            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=bp_case, provider_documents=case_provider)
            treatmentDates = None
            try:
                treatmentDates = TFTreatmentDate.objects.get(for_case_provider=case_provider)
            except:
                pass
            temp_providers.append({
                'provider': case_provider,
                'doc_1': doc1,
                'doc_2': doc2,
                'tf_case_status':case_provider.tf_case_status,
                'treatmentDates':treatmentDates
            })
        except:
            pass
    
    try:
        firm_user = bp_case.firm_users.all()[0]
    except:
        firm_user = None

    provider_cases = []
    request_update = RequestUpdate.objects.get(for_case=bp_case)
    current_date = str(datetime.today().strftime('%m-%d-%Y'))
    date_format = '%m-%d-%Y'
    a = datetime.strptime(current_date, date_format)
    b = datetime.strptime(request_update.status_changed_on, date_format)
    delta = a - b
    print(delta.days)
    temp_delta = 0
    if request_update.isRequested:
        bb = datetime.strptime(request_update.requested_at, date_format)
        temp_delta = a - bb
    if (delta.days > 90 and bp_case.case_status.name != 'New Lead'):
        
        firm_user = bp_case.firm_users.all()
        temp_check = True
        if request_update.isRequested:
            if temp_delta.days > 30:
                temp_check = True
                request_update.isRequested = False
                request_update.save()
            else:
                temp_check = False
        firm_user_name = '-'
        firm_user_extension = '-'
        
        if firm_user:
            firm_user = firm_user[0]
            firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
            
        temp_office_name = ''
        if bp_case.for_client.created_by:
            temp_office_name = bp_case.for_client.created_by.attorneyprofile.office_name
        else:
            temp_office_name = '-'
        
        
        bp_attorney = bp_case.for_client.created_by
        provider_cases.append({
            'id':bp_case.id,
            'client_id':bp_case.for_client.id,
            'client_name': bp_case.for_client.last_name + ", " + bp_case.for_client.first_name,
            'birthday': bp_case.for_client.birthday,
            'incident_date':bp_case.incident_date,
            'case_type':bp_case.case_type.name,
            
            'firm_user_name': firm_user_name,
            'firm_user_extension': firm_user_extension,
            'case_category':bp_case.case_category,
            # 'case_status':bp_case.case_status,
            'date_closed':bp_case.date_closed,
            "office_name":temp_office_name,
            'status':bp_case.case_status.name,
            'recent_status':request_update.recent_status,
            'status_date':request_update.status_changed_on,
            'temp_check': temp_check,
            'isRequested':request_update.isRequested,
            'case_manager':request_update.changed_by,
            'request_count':request_update.request_count

        })
    context = {
        'client':client,
        'case':bp_case,
        'case_providers':temp_providers,
        'locations': locations,
        'case_statuses':case_statuses,
        'user_types':user_types,
        'firm_user':firm_user,
        'tf_notes':tf_notes,
        'provider_users':provider_users,
        'provider_cases':provider_cases,
        'tf_case_status':tf_case_status,
        'tf_accounting':tf_accounting,
        'accounting_doc_1':accounting_doc_1,
        'accounting_doc_2':accounting_doc_2
    }
    return render(request, 'accounts/accountingDetail.html', context)

    
def patientDetail(request, client_id, case_id):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by

    bp_client = BPClient.objects.get(pk=client_id)
    bp_case = BPCase.objects.get(pk=case_id)
    tf_case_status = TFCaseStatus.objects.all()
    case_providers = BPCaseProviders.objects.filter(for_case=bp_case,  provider=userprofile)
    locations = Location.objects.filter(added_by=userprofile)
    case_statuses = BPClientStatus.objects.all()
    user_types = BPAttorneyUserType.objects.all()
    tf_notes = TFNotes.objects.filter(for_case=bp_case)
    provider_users = ProviderStaff.objects.filter(created_by=userprofile)
    print(provider_users)
    temp_providers=[]
    for case_provider in case_providers:
        try:
            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=bp_case, provider_documents=case_provider)
            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=bp_case, provider_documents=case_provider)
            treatmentDates = None
            try:
                treatmentDates = TFTreatmentDate.objects.get(for_case_provider=case_provider)
            except:
                pass
            temp_providers.append({
                'provider': case_provider,
                'doc_1': doc1,
                'doc_2': doc2,
                'tf_case_status':case_provider.tf_case_status,
                'treatmentDates':treatmentDates
            })
        except:
            pass
    
    try:
        firm_user = bp_case.firm_users.all()[0]
    except:
        firm_user = None

    provider_cases = []
    request_update = RequestUpdate.objects.get(for_case=bp_case)
    current_date = str(datetime.today().strftime('%m-%d-%Y'))
    date_format = '%m-%d-%Y'
    a = datetime.strptime(current_date, date_format)
    b = datetime.strptime(request_update.status_changed_on, date_format)
    delta = a - b
    print(delta.days)
    temp_delta = 0
    if request_update.isRequested:
        bb = datetime.strptime(request_update.requested_at, date_format)
        temp_delta = a - bb
    if (delta.days > 90 and bp_case.case_status.name != 'New Lead'):
        
        firm_user = bp_case.firm_users.all()
        temp_check = True
        if request_update.isRequested:
            if temp_delta.days > 30:
                temp_check = True
                request_update.isRequested = False
                request_update.save()
            else:
                temp_check = False
        firm_user_name = '-'
        firm_user_extension = '-'
        
        if firm_user:
            firm_user = firm_user[0]
            firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
            
        temp_office_name = ''
        if bp_case.for_client.created_by:
            temp_office_name = bp_case.for_client.created_by.attorneyprofile.office_name
        else:
            temp_office_name = '-'
        
        
        bp_attorney = bp_case.for_client.created_by
        provider_cases.append({
            'id':bp_case.id,
            'client_id':bp_case.for_client.id,
            'client_name': bp_case.for_client.last_name + ", " + bp_case.for_client.first_name,
            'birthday': bp_case.for_client.birthday,
            'incident_date':bp_case.incident_date,
            'case_type':bp_case.case_type.name,
            
            'firm_user_name': firm_user_name,
            'firm_user_extension': firm_user_extension,
            'case_category':bp_case.case_category,
            # 'case_status':bp_case.case_status,
            'date_closed':bp_case.date_closed,
            "office_name":temp_office_name,
            'status':bp_case.case_status.name,
            'recent_status':request_update.recent_status,
            'status_date':request_update.status_changed_on,
            'temp_check': temp_check,
            'isRequested':request_update.isRequested,
            'case_manager':request_update.changed_by,
            'request_count':request_update.request_count

        })



    print(temp_providers)
    context = {
        'client':bp_client,
        'case':bp_case,
        'case_providers':temp_providers,
        'locations': locations,
        'case_statuses':case_statuses,
        'user_types':user_types,
        'firm_user':firm_user,
        'tf_notes':tf_notes,
        'provider_users':provider_users,
        'provider_cases':provider_cases,
        'tf_case_status':tf_case_status
    }
    return render(request, 'accounts/patientDetail.html', context)

@xframe_options_sameorigin
def open_file(request, doc_id):
    print('open_file')
    doc = None
    try:
        doc = BPDoc.objects.get(pk=doc_id)
    except:
        doc = TFDoc.objects.get(pk=doc_id)
    file_path = doc.upload.url
    print(file_path)
    print('hello')
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = base_dir + file_path
    thefile = file_path
    filename = os.path.basename(thefile)
    chunk_size = 20480
    response = StreamingHttpResponse(FileWrapper(open(thefile, 'rb'), chunk_size),
        content_type=mimetypes.guess_type(thefile)[0])
    response['Content-Length'] = os.path.getsize(thefile)
    response['Content-Disposition'] = "filename=%s" % filename

    return response

def close(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:

        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, open='False')
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def openfilter(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:

        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, open='True')
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def newLead(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:
        case_status = BPClientStatus.objects.get(name__icontains='New Lead')
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, case_status=case_status)
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def paid(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:
        case_status = BPClientStatus.objects.get(name__icontains='Paid')
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, case_status=case_status)
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def settled(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:
        case_status = BPClientStatus.objects.get(name__icontains='Settled')
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, case_status=case_status)
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def settlement(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:
        case_status = BPClientStatus.objects.get(name__icontains='Settlement')
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, case_status=case_status)
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def litigation(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:
        case_status = BPClientStatus.objects.get(name__icontains='Litigation')
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, case_status=case_status)
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def treatmentDone(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:
        case_status = BPClientStatus.objects.get(name__icontains='Treatment Done')
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, case_status=case_status)
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def treating(request, check=False):

    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    temp = []
    provider_cases = []
    perform_search = False
    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    for location in locations:
        specialties = location.specialties.all()
        for specialty in specialties:

            temp.append({
                'provider': userprofile,
                'location': location,
                'specialty': specialty
            })

    bp_attorneys = None
    temp_attorneys = BPAttorney.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        search_clients = request.POST.get('search_clients')
        value = request.POST.get('value')
        print(value)
        if value == 'True':
            check=True
        print(search)
        print(search_clients)
        if search_clients == '':
            bp_attorneys = BPAttorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
            temp_clients = []
            for att in bp_attorneys:
                clients = BPClient.objects.filter(created_by=att)
                for client in clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        elif search == '':
            bp_clients = BPClient.objects.filter(Q(first_name__icontains=search_clients)|Q(last_name__icontains=search_clients))
            for client in bp_clients:
                    cases = BPCase.objects.filter(for_client=client)

                    for case in cases:
                        case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                        print('cases & case_providers', case, case_providers)
                        for case_provider in case_providers:
                            case = BPCase.objects.get(pk=case_provider.for_case.id)
                            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                            provider_cases.append({
                                'id':case.id,
                                'client_id':case.for_client.id,
                                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                                'birthday': case.for_client.birthday,
                                'incident_date':case.incident_date,
                                'case_type':case.case_type.name,
                                'doc_1':doc1,
                                'doc_2':doc2,
                                'case_category':case.case_category,
                                'case_status':case.case_status,
                                'date_closed':case.date_closed,
                                "office_name":case.for_client.created_by.attorneyprofile.office_name,
                                'status':case.case_status.name
                            })
        perform_search = True
    if not perform_search:
        case_status = BPClientStatus.objects.get(name__icontains='Treating')
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            try:
                case = BPCase.objects.get(pk=case_provider.for_case.id, case_status=case_status)
                doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
                doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
                temp_office_name = ''
                if case.for_client.created_by:
                    temp_office_name = case.for_client.created_by.attorneyprofile.office_name
                else:
                    temp_office_name = '-'
                provider_cases.append({
                    'id':case.id,
                    'client_id':case.for_client.id,
                    'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                    'birthday': case.for_client.birthday,
                    'incident_date':case.incident_date,
                    'case_type':case.case_type.name,
                    'doc_1':doc1,
                    'doc_2':doc2,
                    'case_category':case.case_category,
                    'case_status':case.case_status,
                    'date_closed':case.date_closed,
                    "office_name":temp_office_name,
                    'status':case.case_status.name
                })
            except:
                pass


    print('case_providers', provider_cases)
    context = {
        'temp':temp,
        'userprofile': userprofile,
        'provider_cases':provider_cases,
        'bp_attorneys':bp_attorneys,
        'check':check,
        'temp_attorneys':temp_attorneys,
        'client_statuses':client_statuses
    }
    return render(request, 'accounts/case_management.html', context)

def generateReport(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    
    
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


def reports(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    tf_case_statutes = TFCaseStatus.objects.all()
    
    case_providers = BPCaseProviders.objects.filter(provider=userprofile)
    check = False
    records = []
    if request.method == 'POST':
        date = request.POST.get('date')
        print('this is date', date)
        date_selection = request.POST.get('date_selection')
        print('this is date_selection', date_selection)
        first_date = request.POST.get('first_date')
        print('this is first_date', first_date)
        end_date = request.POST.get('end_date')
        print('this is end_date', end_date)
        law_firm = request.POST.get('law_firm')
        print('this is law_firm', law_firm)
        case_statuses = request.POST.getlist('case_statuses')
        print('this is case_statuses:', case_statuses)
        report_type = request.POST.get('report_type')
        
        date_format = '%Y-%m-%d'
        if law_firm != '':
            bp_attorney = BPAttorney.objects.get(pk=int(law_firm))
            
            clients = BPClient.objects.filter(created_by=bp_attorney)
            for client in clients:
                cases = BPCase.objects.filter(for_client=client)

                for case in cases:
                    case_providers = BPCaseProviders.objects.filter(provider=userprofile, for_case=case)
                    print('cases & case_providers', case, case_providers)
                    paid_visits = -1
                    temp_check = False
                    index = 1
                    for case_provider in case_providers:
                        tf_treatment_date = None
                        tf_accounting = None
                        if report_type == 'payment_received':
                            print('hello')
                            try:
                                tf_accounting = TFAccounting.objects.get(~Q(payment_received_date='_/_/_'),created_by=userprofile, for_case_provider=case_provider, )
                                
                            except:
                                pass
                        else:
                            try:
                                tf_accounting = TFAccounting.objects.get(payment_received_date='_/_/_',created_by=userprofile, for_case_provider=case_provider, )
                            except:
                                pass
                        
                        try:
                            tf_treatment_date = TFTreatmentDate.objects.get(created_by=userprofile, for_case_provider=case_provider)
                        except:
                            pass
                        
                        if tf_accounting and tf_treatment_date and tf_treatment_date.visits != '__':
                            paid_visits = float(float(tf_accounting.final) / float(tf_treatment_date.visits))
                            paid_visits = '{:.2f}'.format(paid_visits)
                            print(paid_visits)
                        c = ''
                        if date == 'first_visit' and tf_treatment_date and tf_treatment_date.first_date != '_/_/_': 
                            c = datetime.strptime(tf_treatment_date.first_date, date_format)
                        elif date == 'last_visit' and tf_treatment_date and tf_treatment_date.second_date != '_/_/_':
                            c = datetime.strptime(tf_treatment_date.first_date, date_format)
                        elif date == 'injury_date':
                            incident_date = case_provider.for_case.incident_date

                            c = datetime.strptime(incident_date, date_format)
                        if c != '':
                            if first_date != '' and end_date != '':
                                
                                a = datetime.strptime(first_date, date_format)
                                b = datetime.strptime(end_date, date_format)
                                
                                
                                if c >= a and c<=b:
                                    records.append({
                                        'attorney':bp_attorney,
                                        'treatmentDates':tf_treatment_date,
                                        'tf_accounting':tf_accounting,
                                        'provider':case_provider,
                                        'client':client,
                                        'paid_visits':paid_visits,
                                        'index': index,
                                    })
                                    index += 1
                            elif first_date != '' and end_date == '':
                                a = datetime.strptime(first_date, date_format)
                                current_date = str(datetime.today().strftime('%Y-%m-%d'))
                                current_date = datetime.strptime(current_date, date_format)
                                if c >= a and c <= current_date:
                                    
                                    records.append({
                                        'attorney':bp_attorney,
                                        'treatmentDates':tf_treatment_date,
                                        'tf_accounting':tf_accounting,
                                        'provider':case_provider,
                                        'client':client,
                                        'paid_visits':paid_visits,
                                        'index': index,
                                    })
                                    index += 1
                            elif first_date == '' and end_date != '':
                                first_date = '2000-01-01'
                                a = datetime.strptime(first_date, date_format)
                                b = datetime.strptime(end_date, date_format)
                                if c>=a and c<=b:
                                    
                                    records.append({
                                        'attorney':bp_attorney,
                                        'treatmentDates':tf_treatment_date,
                                        'tf_accounting':tf_accounting,
                                        'provider':case_provider,
                                        'client':client,
                                        'paid_visits':paid_visits,
                                        'index': index,
                                    })
                                    index += 1
                            elif first_date == '' and end_date == '':
                                a = ''
                                b = ''
                                temp_check = False
                                if date_selection == 'current_month':
                                    today = datetime.today()
                                    first_date = str(datetime(today.year, today.month, 1).strftime('%Y-%m-%d'))
                                    a = datetime.strptime(first_date, date_format)
                                    current_date = str(datetime.today().strftime('%Y-%m-%d'))
                                    b = datetime.strptime(current_date, date_format)
                                elif date_selection == 'last_month':
                                    last_day_of_prev_month = dt.date.today().replace(day=1) - dt.timedelta(days=1)

                                    start_day_of_prev_month = str(dt.date.today().replace(day=1) - dt.timedelta(days=last_day_of_prev_month.day))
                                    a = datetime.strptime(str(last_day_of_prev_month), date_format)
                                    b = datetime.strptime(start_day_of_prev_month, date_format)
                                elif date_selection == 'current_quarter':
                                    current_date = datetime.now()
                                    current_quarter = int((current_date.month - 1) / 3 + 1)
                                    first_date = str(datetime(current_date.year, 3 * current_quarter - 2, 1).strftime('%Y-%m-%d'))
                                    last_date =str((datetime(current_date.year, 3 * current_quarter + 1, 1) + dt.timedelta(days=-1)).strftime('%Y-%m-%d'))
                                    a = datetime.strptime(str(first_date), date_format)
                                    b = datetime.strptime(str(last_date), date_format)
                                    
                                elif date_selection == 'last_quarter':
                                    current_date = datetime.now()
                                    last_quarter = int((current_date.month - 1) / 3 + 1) - 1
                                    first_date = str(datetime(current_date.year, 3 * last_quarter - 2, 1).strftime('%Y-%m-%d'))
                                    last_date =str((datetime(current_date.year, 3 * last_quarter + 1, 1) + dt.timedelta(days=-1)).strftime('%Y-%m-%d'))
                                    a = datetime.strptime(str(first_date), date_format)
                                    b = datetime.strptime(str(last_date), date_format)
                                    
                                elif date_selection == 'current_year':
                                    # starting_day_of_current_year = datetime.now().date().replace(month=1, day=1).strftime('%Y-%m-%d')  
                                    # ending_day_of_current_year = datetime.now().date().replace(month=12, day=31).strftime('%Y-%m-%d')

                                    starting_day_of_current_year = str(dt.date.today().replace(month=1, day=1))
                                    ending_day_of_current_year = str(dt.date.today().replace(month=12, day=31))
                                    print(starting_day_of_current_year)
                                    a = datetime.strptime(str(starting_day_of_current_year), date_format)
                                    b = datetime.strptime(str(ending_day_of_current_year), date_format)
                                    
                                elif date_selection == 'last_year':
                                    starting_day_of_current_year = str(dt.date.today().replace(month=1, day=1) - dt.timedelta(days=365))
                                    ending_day_of_current_year = str(dt.date.today().replace(month=12, day=31)- dt.timedelta(days=365))
                                    print(starting_day_of_current_year)
                                    a = datetime.strptime(str(starting_day_of_current_year), date_format)
                                    b = datetime.strptime(str(ending_day_of_current_year), date_format)
                                    print(a)
                                    print(b)
                                elif date_selection == 'all_time':
                                    temp_check = True
                                if not temp_check:
                                    if report_type == 'payment_received' and tf_accounting and tf_accounting.payment_received_date != '_/_/_':   
                                        if c >= a and c <= b:
                                            
                                            records.append({
                                                'attorney':bp_attorney,
                                                'treatmentDates':tf_treatment_date,
                                                'tf_accounting':tf_accounting,
                                                'provider':case_provider,
                                                'client':client,
                                                'paid_visits':paid_visits,
                                                'index': index,
                                            })
                                            index += 1
                                    elif report_type == 'accounts_receivable' and tf_accounting and tf_accounting.payment_received_date == '_/_/_':
                                        if c >= a and c <= b:
                                            
                                            records.append({
                                                'attorney':bp_attorney,
                                                'treatmentDates':tf_treatment_date,
                                                'tf_accounting':tf_accounting,
                                                'provider':case_provider,
                                                'client':client,
                                                'paid_visits':paid_visits,
                                                'index': index,
                                            })
                                            index += 1
                                else:

                                    records.append({
                                                    'attorney':bp_attorney,
                                                    'treatmentDates':tf_treatment_date,
                                                    'tf_accounting':tf_accounting,
                                                    'provider':case_provider,
                                                    'client':client,
                                                    'paid_visits':paid_visits,
                                                    'index': index,
                                                }) 
                                    index += 1

        elif law_firm == '':
            index = 1
            case_providers = BPCaseProviders.objects.filter(provider=userprofile)
            for case_provider in case_providers:
                case = BPCase.objects.get(pk=case_provider.for_case.id)
                bp_attorney = case.for_client.created_by
                x_check = False
                paid_visits = -1
                
                for x in records:
                    if x['id'] == case.id:
                        x_check = True
                        break
                if not x_check:
                    tf_treatment_date = None
                    tf_accounting = None
                    if report_type == 'payment_received':
                        print('hello')
                        try:
                            tf_accounting = TFAccounting.objects.get(~Q(payment_received_date='_/_/_'),created_by=userprofile, for_case_provider=case_provider, )
                        except:
                            pass
                    else:
                        try:
                            tf_accounting = TFAccounting.objects.get(payment_received_date='_/_/_',created_by=userprofile, for_case_provider=case_provider, )
                        except:
                            pass
                    
                    try:
                        tf_treatment_date = TFTreatmentDate.objects.get(created_by=userprofile, for_case_provider=case_provider)
                    except:
                        pass

                    if tf_accounting and tf_treatment_date and tf_treatment_date.visits != '__':
                            paid_visits = float(float(tf_accounting.final) / float(tf_treatment_date.visits))
                            paid_visits = '{:.2f}'.format(paid_visits)
                            print(paid_visits)
                    
                    c = ''
                    if date == 'first_visit' and tf_treatment_date and tf_treatment_date.first_date != '_/_/_': 
                        c = datetime.strptime(tf_treatment_date.first_date, date_format)
                    elif date == 'last_visit' and tf_treatment_date and tf_treatment_date.second_date != '_/_/_':
                        c = datetime.strptime(tf_treatment_date.first_date, date_format)
                    elif date == 'injury_date':
                        incident_date = case_provider.for_case.incident_date

                        c = datetime.strptime(incident_date, date_format)
                    if c != '':
                        if first_date != '' and end_date != '':
                            
                            a = datetime.strptime(first_date, date_format)
                            b = datetime.strptime(end_date, date_format)
                            
                            
                            if c >= a and c<=b:
                                records.append({
                                    'attorney':bp_attorney,
                                    'treatmentDates':tf_treatment_date,
                                    'tf_accounting':tf_accounting,
                                    'provider':case_provider,
                                    'client':case.for_client,
                                    'id':case.id,
                                    'index':index,
                                    'paid_visits':paid_visits
                                })
                                index += 1
                        elif first_date != '' and end_date == '':
                            a = datetime.strptime(first_date, date_format)
                            current_date = str(datetime.today().strftime('%Y-%m-%d'))
                            current_date = datetime.strptime(current_date, date_format)
                            if c >= a and c <= current_date:
                                
                                records.append({
                                    'attorney':bp_attorney,
                                    'treatmentDates':tf_treatment_date,
                                    'tf_accounting':tf_accounting,
                                    'provider':case_provider,
                                    'client':case.for_client,
                                    'id':case.id,
                                    'index':index,
                                    'paid_visits':paid_visits
                                })
                                index += 1
                        elif first_date == '' and end_date != '':
                            first_date = '2000-01-01'
                            a = datetime.strptime(first_date, date_format)
                            b = datetime.strptime(end_date, date_format)
                            if c>=a and c<=b:
                                
                                records.append({
                                    'attorney':bp_attorney,
                                    'treatmentDates':tf_treatment_date,
                                    'tf_accounting':tf_accounting,
                                    'provider':case_provider,
                                    'client':case.for_client,
                                    'id':case.id,
                                    'index':index,
                                    'paid_visits':paid_visits
                                })
                                index += 1
                        elif first_date == '' and end_date == '':
                            a = ''
                            b = ''
                            temp_check = False
                            if date_selection == 'current_month':
                                today = datetime.today()
                                first_date = str(datetime(today.year, today.month, 1).strftime('%Y-%m-%d'))
                                a = datetime.strptime(first_date, date_format)
                                current_date = str(datetime.today().strftime('%Y-%m-%d'))
                                b = datetime.strptime(current_date, date_format)
                            elif date_selection == 'last_month':
                                last_day_of_prev_month = dt.date.today().replace(day=1) - dt.timedelta(days=1)

                                start_day_of_prev_month = str(dt.date.today().replace(day=1) - dt.timedelta(days=last_day_of_prev_month.day))
                                a = datetime.strptime(str(last_day_of_prev_month), date_format)
                                b = datetime.strptime(start_day_of_prev_month, date_format)
                            elif date_selection == 'current_quarter':
                                current_date = datetime.now()
                                current_quarter = int((current_date.month - 1) / 3 + 1)
                                first_date = str(datetime(current_date.year, 3 * current_quarter - 2, 1).strftime('%Y-%m-%d'))
                                last_date =str((datetime(current_date.year, 3 * current_quarter + 1, 1) + dt.timedelta(days=-1)).strftime('%Y-%m-%d'))
                                a = datetime.strptime(str(first_date), date_format)
                                b = datetime.strptime(str(last_date), date_format)
                                
                            elif date_selection == 'last_quarter':
                                current_date = datetime.now()
                                last_quarter = int((current_date.month - 1) / 3 + 1) - 1
                                first_date = str(datetime(current_date.year, 3 * last_quarter - 2, 1).strftime('%Y-%m-%d'))
                                last_date =str((datetime(current_date.year, 3 * last_quarter + 1, 1) + dt.timedelta(days=-1)).strftime('%Y-%m-%d'))
                                a = datetime.strptime(str(first_date), date_format)
                                b = datetime.strptime(str(last_date), date_format)
                                
                            elif date_selection == 'current_year':
                                # starting_day_of_current_year = datetime.now().date().replace(month=1, day=1).strftime('%Y-%m-%d')  
                                # ending_day_of_current_year = datetime.now().date().replace(month=12, day=31).strftime('%Y-%m-%d')

                                starting_day_of_current_year = str(dt.date.today().replace(month=1, day=1))
                                ending_day_of_current_year = str(dt.date.today().replace(month=12, day=31))
                                print(starting_day_of_current_year)
                                a = datetime.strptime(str(starting_day_of_current_year), date_format)
                                b = datetime.strptime(str(ending_day_of_current_year), date_format)
                                
                            elif date_selection == 'last_year':
                                starting_day_of_current_year = str(dt.date.today().replace(month=1, day=1) - dt.timedelta(days=365))
                                ending_day_of_current_year = str(dt.date.today().replace(month=12, day=31)- dt.timedelta(days=365))
                                print(starting_day_of_current_year)
                                a = datetime.strptime(str(starting_day_of_current_year), date_format)
                                b = datetime.strptime(str(ending_day_of_current_year), date_format)
                                print(a)
                                print(b)
                            elif date_selection == 'all_time':
                                temp_check = True
                            if not temp_check:
                                if report_type == 'payment_received' and tf_accounting and tf_accounting.payment_received_date != '_/_/_':   
                                    if c >= a and c <= b:
                                        
                                        records.append({
                                            'attorney':bp_attorney,
                                            'treatmentDates':tf_treatment_date,
                                            'tf_accounting':tf_accounting,
                                            'provider':case_provider,
                                            'client':case.for_client,
                                            'id':case.id,
                                            'index':index,
                                            'paid_visits':paid_visits
                                        })
                                        index += 1
                                elif report_type == 'accounts_receivable' and tf_accounting and tf_accounting.payment_received_date == '_/_/_':
                                    if c >= a and c <= b:
                                        
                                        records.append({
                                            'attorney':bp_attorney,
                                            'treatmentDates':tf_treatment_date,
                                            'tf_accounting':tf_accounting,
                                            'provider':case_provider,
                                            'client':case.for_client,
                                            'id':case.id,
                                            'index':index,
                                            'paid_visits':paid_visits
                                        })
                                        index += 1
                            else:

                                records.append({
                                                'attorney':bp_attorney,
                                                'treatmentDates':tf_treatment_date,
                                                'tf_accounting':tf_accounting,
                                                'provider':case_provider,
                                                'client':case.for_client,
                                                'id':case.id,
                                                'index':index,
                                                'paid_visits':paid_visits
                                            })
                                index += 1

                        



        check = True

    context = {
        'tf_case_statutes':tf_case_statutes,
        'case_providers': case_providers,
        'check':check,
        'records':records
    }
    return render(request, 'accounts/reports.html', context)


def accounting(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by

    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    case_types = BPCaseType.objects.all()
    tf_case_status = TFCaseStatus.objects.all()
    context = {
        'userprofile': userprofile,
        'locations': locations,
        'client_statuses': client_statuses,
        'case_types':case_types,
        'tf_case_status':tf_case_status
    }
    return render(request, 'accounts/accounting.html', context)

def case_management(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by

    locations = Location.objects.filter(added_by=userprofile)
    client_statuses = BPClientStatus.objects.all()
    tf_case_status = TFCaseStatus.objects.all()
    case_types = BPCaseType.objects.all()
    context = {
        'userprofile': userprofile,
        'locations': locations,
        'client_statuses': client_statuses,
        'case_types':case_types,
        'tf_case_status':tf_case_status
    }

    return render(request, 'accounts/case_management.html', context)

def addNewFirm(request, client_id, case_id):
    if request.method == "POST":
        # try:
            office_name = request.POST.get('office_name')
            email1 = request.POST.get('email1')
            username1 = request.POST.get('username1')
            password1 = request.POST.get('password1')
            address1 = request.POST.get('address1')
            address2 = request.POST.get('address2')
            city = request.POST.get('city')
            state = request.POST.get('state')
            post_code = request.POST.get('post_code')
            user_type1 = request.POST.get('user_type1')
            user_type1= BPAttorneyUserType.objects.get(pk=int(user_type1))

            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            user_type = request.POST.get('user_type')
            phone_extension = request.POST.get('phone_extension')
            user_type= BPAttorneyUserType.objects.get(pk=int(user_type))

            hashed_pwd = make_password(password1)
            user = User.objects.create(username=username1, email=email1, password=hashed_pwd)
            userprofile = BPFirm.objects.create(user = user, office_name=office_name, account_type='Attorney')
            userprofile.save()


            attorney = BPAttorney.objects.create(attorneyprofile=userprofile,  user_type=user_type1)
            attorney.save()
            attorney_location = BPAttorneyLocation.objects.create(added_by=attorney,address=address1,address2=address2, city=city, state=state, post_code=post_code,
                        email=email1)
            attorney_location.save()

            hashed_pwd = make_password(password)
            user = User.objects.create(username=username, email=email, password=hashed_pwd, first_name=first_name, last_name=last_name)
            user.save()
            staff = BPAttorneyStaff.objects.create(user=user, created_by=attorney, user_type=user_type, phone_extension=phone_extension)
            staff.save()

            messages.success(request, 'Attorney and Firm User has been added successfully!')
        # except:
            messages.error(request, 'Operation Failed! Please try again.')

    return redirect('patientDetail', int(client_id), int(case_id))





class ListAllPatients(APIView):
    def get(self, request):
        try:
            profile = Firm.objects.get(user=request.user, account_type='Provider')
            userprofile = Provider.objects.get(providerprofile=profile)

        except:
            userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
            userprofile = userprofile.created_by

        provider_cases = []
        case_providers = BPCaseProviders.objects.filter(provider=userprofile)
        for case_provider in case_providers:
            case = BPCase.objects.get(pk=case_provider.for_case.id)
            doc1 = BPDoc.objects.get(document_no='TF Bills', for_case=case, provider_documents=case_provider)
            doc2 = BPDoc.objects.get(document_no='TF Rec', for_case=case, provider_documents=case_provider)
            doc1_serializer = DocSerializer(doc1, many=False)
            doc2_serializer = DocSerializer(doc2, many=False)
            bp_attorney = case.for_client.created_by
            attorney_location = BPAttorneyLocation.objects.filter(added_by=bp_attorney)

            firm_user = case.firm_users.all()
            loc = LocationSerializer(case_provider.location, many=False)
            spec = SpecialtySerializer(case_provider.specialty, many=False)

            attorney_phone_number = '-'
            firm_user_name = '-'
            firm_user_extension = '-'
            if attorney_location:
                attorney_location = attorney_location[0]
                attorney_phone_number = attorney_location.phone
            if firm_user:
                firm_user = firm_user[0]
                firm_user_name = firm_user.user.first_name + ' ' + firm_user.user.last_name
                firm_user_extension = firm_user.phone_extension
            temp_office_name = ''
            if case.for_client.created_by:
                temp_office_name = case.for_client.created_by.attorneyprofile.office_name
            else:
                temp_office_name = '-'
            provider_cases.append({
                'id':case.id,
                'client_id':case.for_client.id,
                'client_name': case.for_client.last_name + " " + case.for_client.first_name,
                'birthday': case.for_client.birthday,
                'incident_date':case.incident_date,
                'case_type':case.case_type.name,
                'doc_1':doc1_serializer.data,
                'doc_2':doc2_serializer.data,
                'address': loc.data,
                'specialty': spec.data,
                'attorney_phone_number': attorney_phone_number,
                'firm_user_name': firm_user_name,
                'firm_user_extension': firm_user_extension,
                'case_category':case.case_category,
                # 'case_status':case.case_status,
                'date_closed':case.date_closed,
                "office_name":temp_office_name,
                'status':case.case_status.name
            })

        context = {
                    'response': provider_cases
                }
        return Response(context)

def attachAttorney(request):
    # try:
    if request.method == 'POST':
        attorney = request.POST.get('attorney')
        print(attorney)
        client_id = request.POST.get('client_id')
        attorney = BPAttorney.objects.get(pk=int(attorney))

        client = BPClient.objects.get(pk=int(client_id))
        client.created_by = attorney
        client.save()
        messages.success(request, 'Attorney has been attached successfully')
        print(attorney)
        print(client_id)
    # except:
    #     messages.error(request, 'Operation Failed! Please try again!')
    return redirect('case_management')

def TFUpload(request, client_id, case_id, doc_id):
    # print(request.FILES)
    client = BPClient.objects.get(pk=client_id)
    case = BPCase.objects.get(pk=case_id)
    doc = TFDoc.objects.get(pk=doc_id)
    if request.method == 'POST':
        my_file = request.FILES.get('file')
        name = request.POST.get('name')
        document_type = request.POST.get('documentType')
        print(document_type)
        print(name)
        doc.upload = my_file
        doc.file_name = name
        doc.check='True'
        doc.save()
        print('this is the doc link :', doc.upload.url)
        return HttpResponse('')
    else:
        JsonResponse({'post':'false'})

def upload(request, client_id, case_id, doc_id):
    # print(request.FILES)
    client = BPClient.objects.get(pk=client_id)
    case = BPCase.objects.get(pk=case_id)
    doc = None
    try:
        doc = BPDoc.objects.get(pk=doc_id)
    except:
        doc = TFDoc.objects.get(pk=doc_id)
    if request.method == 'POST':
        my_file = request.FILES.get('file')
        name = request.POST.get('name')
        document_type = request.POST.get('documentType')
        print(document_type)
        print(name)
        doc.upload = my_file
        doc.file_name = name
        doc.check='True'
        doc.save()
        print('this is the doc link :', doc.upload.url)
        return HttpResponse('')
    else:
        JsonResponse({'post':'false'})

def case_add_attorney(request):

    account_type = 'Attorney'
    if request.method == 'POST':

        try:

            office_name = request.POST.get('office_name')
            # last_name = request.POST.get('last_name')
            # email = request.POST.get('email')
            # user_type = request.POST.get('user_type')

            address1 = request.POST.get('address1')
            city1 = request.POST.get('city1')
            state1 = request.POST.get('state1')
            # country1 = request.POST.get('country1')
            address3 = request.POST.get('address3')
            postal1 = request.POST.get('postal1')

            phone1 = request.POST.get('phone1')
            # fax1 = request.POST.get('fax1')
            firm_username = request.POST.get('firm_username')
            firm_first_name = request.POST.get('firm_first_name')
            firm_last_name = request.POST.get('firm_last_name')
            firm_phone_extension = request.POST.get('firm_phone_extension')
            firm_email = request.POST.get('firm_email')



            S=15
            username = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
            password = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
            hashed_pwd = make_password(password)

            user = User.objects.create(username=username, password=hashed_pwd)
            user.save()


            # account_type = request.POST.get('account_type', 'Provider')
            userprofile = BPFirm.objects.create(user = user, office_name=office_name, account_type=account_type)
            userprofile.save()
            attorney = None
            if account_type == 'Attorney':
                attorney = BPAttorney.objects.create(attorneyprofile=userprofile)
                attorney.save()
            attorney_location = BPAttorneyLocation.objects.create(added_by=attorney,address=address1,address2=address3, city=city1, state=state1, post_code=postal1,
                        phone=phone1)
            attorney_location.save()

            S=15
            
            password = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
            hashed_pwd = make_password(password)

            user = User.objects.create(username=firm_username, password=hashed_pwd, first_name=firm_first_name, last_name=firm_last_name)
            user.save()
            user_type = BPAttorneyUserType.objects.get(name='case manager')
            firm_user = BPAttorneyStaff.objects.create(created_by=attorney, user=user, phone_extension=firm_phone_extension,user_type=user_type)
            firm_user.save()
            messages.success(request, 'Attorney & Firm user has been created successfully!')
            return redirect('case_management')
        except:
            messages.error(request, 'Operation Failed! Please try again.')


    return render(request, 'accounts/case_add_attorneys.html')

# def advance_filters(request):
#     list_of_ids = []
#     temp_list = []
#     list_of_distance = []
#     obj = None
#     check = True
#     not_found = False
#     temp_locations = []
#     actual_locations = []
#     favorite_locations = []
#     favorites = None
#     actual_provider_locations = []
#     profile = None
#     try:
#         profile = Firm.objects.get(user=request.user)
#         if profile.account_type == 'Attorney':
#             userprofile = Attorney.objects.get(attorneyprofile=profile)
#     except:
#         userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
#         userprofile = userprofile.created_by

#     favorites = userprofile.favorites.all()
#     blacklist_users = userprofile.blacklist.all()
#     flagged_users = userprofile.flag.all()
#     try:
#         if request.method == "POST":
#             specialty = request.POST.get('specialty')
#             address = request.POST.get('address')
#             city = request.POST.get('city')
#             state = request.POST.get('state')
#             postal = request.POST.get('postal')

#             input_address = str(address) + str(city) + str(state) + str(postal)
#             print(input_address)

#             obj = Specialty.objects.get(name__icontains=specialty)

#             api_key = 'AIzaSyBqxc6kyS-LoyaHvVca125NQMefYWI3bn8'
#             gmaps_client = googlemaps.Client(api_key)
#             geocode_result = gmaps_client.geocode(input_address)
#             result = geocode_result[0]

#             input_latitude = result['geometry']['location']['lat']
#             input_longitude = result['geometry']['location']['lng']


#             print(input_latitude, input_longitude)

#             print(obj.name)

#             print('its the specialty')

#             locations = Location.objects.filter(specialties=obj)
#             print(locations)
#             for location in locations:
#                 p = pi/180
#                 a = 0.5 - cos((input_latitude-float(location.latitude))*p)/2 + cos(float(location.latitude)*p) * cos(input_latitude*p) * (1-cos((input_longitude-float(location.longitude))*p))/2
#                 distance =  12742 * asin(sqrt(a)) #2*R*asin...
#                 print(distance)
#                 if distance <= obj.radius:
#                     print('location', location.id)
#                     check_temp = False
#                     check_flag = False
#                     for blacklist in blacklist_users:
#                         if location.added_by.id == blacklist.id:
#                             check_temp = True
#                     for flagged in flagged_users:
#                         if location.added_by.id == flagged.provider.id:
#                             check_flag = True
#                     if not check_temp:
#                         try:
#                             fav_loc = favorites.get(provider=location.added_by, location=location, specialty=obj)
#                             favorite_locations.append({

#                                 'provider': location.added_by,
#                                 'obj': obj,
#                                 'location': location,
#                                 'distance':distance,
#                                 'blacklist': False,
#                             })
#                         except:
#                             #list_of_ids.append(location.id)
#                             # print('this is location list -----', list_of_ids)
#                             # list_of_distance.append(distance)

#                             actual_locations.append({

#                                 'provider': location.added_by,
#                                 'obj': obj,
#                                 'location': location,
#                                 'distance': distance,
#                                 'blacklist': False,
#                             })
#                     else:
#                         actual_locations.append({

#                                 'provider': location.added_by,
#                                 'obj': obj,
#                                 'location': location,
#                                 'distance': distance,
#                                 'blacklist': True,
#                             })
#                 else:
#                     check_temp = False
#                     for blacklist in blacklist_users:
#                         if location.added_by.id == blacklist.id:
#                             check_temp = True
#                     if not check_temp:
#                         temp_list.append({

#                             'provider': location.added_by,
#                             'obj': obj,
#                             'location': location,
#                             'distance':distance,
#                             'blacklist': False,

#                         })
#                     else:
#                         temp_list.append({

#                             'provider': location.added_by,
#                             'obj': obj,
#                             'location': location,
#                             'distance':distance,
#                             'blacklist': True,

#                         })
#             print('unsorted', temp_list)
#             if len(actual_locations) == 0:
#                 not_found = True
#                 temp_list = sorted(temp_list, key=lambda o: o['distance'])

#                 # for i in range(3):
#                 #     list_of_ids.append(sorted_cards[i]['id'])
#                 #     list_of_distance.append(sorted_cards[i]['distance'])
#                 #     x = Location.objects.get(pk=sorted_cards[i]['id'])
#                 #     temp_locations.append(x)
#                 temp_list = temp_list[:3]
#     except:
#         messages.error(request, 'Please enter the correct specialty along with address!')

#     if not_found:
#         actual_locations = temp_list

#     else:

#         actual_locations = sorted(actual_locations, key=lambda o: o['distance'])
#     specialties = Specialty.objects.all()

#     favorite_locations = sorted(favorite_locations, key=lambda o: o['distance'])
#     context = {
#         'specialties': specialties,
#         'actual_locations': actual_locations,
#         'obj': obj,
#         'check': check,
#         'actual_provider_locations': actual_provider_locations,
#         'favorite_locations': favorite_locations
#     }
#     return render(request, 'accounts/filters.html', context)

# def filters(request):
#     name = ''
#     list_of_ids = []
#     temp_list = []
#     list_of_distance = []
#     obj = None
#     check = False
#     temp_locations = []
#     actual_locations = []
#     not_found = False
#     favorite_locations = []
#     favorites = None


#     profile = Firm.objects.get(user=request.user)
#     if profile.account_type == 'Attorney':
#         userprofile = Attorney.objects.get(attorneyprofile=profile)
#         favorites = userprofile.favorites.all()
#         blacklist_users = userprofile.blacklist.all()
#     try:
#         if request.method == 'POST':
#             name = request.POST.get('name')

#             data = name.split() #split string into a list
#             obj = None

#             for temp in data:
#                 try:
#                     obj = Specialty.objects.get(name__icontains=temp)
#                     if obj:
#                         data.remove(temp)
#                         check = True
#                         break
#                 except:
#                     try:
#                         obj = Provider.objects.get(first_name__iexact=temp)
#                         if obj:
#                             data.remove(temp)
#                             break
#                     except:
#                         pass

#             input_address = ''
#             for elem in data:
#                 input_address += elem
#                 input_address += ' '

#             api_key = 'AIzaSyBqxc6kyS-LoyaHvVca125NQMefYWI3bn8'
#             gmaps_client = googlemaps.Client(api_key)
#             geocode_result = gmaps_client.geocode(input_address)
#             result = geocode_result[0]

#             input_latitude = result['geometry']['location']['lat']
#             input_longitude = result['geometry']['location']['lng']


#             print(input_latitude, input_longitude)



#             if check:
#                 print(obj.name)
#                 print(data)
#                 print('its the specialty')
#                 locations = Location.objects.filter(specialties=obj)
#                 print(locations)
#                 for location in locations:
#                     p = pi/180
#                     a = 0.5 - cos((input_latitude-float(location.latitude))*p)/2 + cos(float(location.latitude)*p) * cos(input_latitude*p) * (1-cos((input_longitude-float(location.longitude))*p))/2
#                     distance =  12742 * asin(sqrt(a)) #2*R*asin...
#                     print(distance)
#                     if distance <= obj.radius:
#                         check_temp = False
#                         for blacklist in blacklist_users:
#                             if location.added_by.id == blacklist.id:
#                                 check_temp = True
#                         if not check_temp:
#                             try:
#                                 fav_loc = favorites.get(provider=location.added_by, location=location, specialty=obj)
#                                 favorite_locations.append({
#                                     'provider': location.added_by,
#                                     'obj': obj,
#                                     'location': location,
#                                     'distance':distance
#                                 })
#                             except:
#                                 #list_of_ids.append(location.id)
#                                 # print('this is location list -----', list_of_ids)
#                                 # list_of_distance.append(distance)
#                                 actual_locations.append({
#                                     'id': location.id,
#                                     'distance': distance
#                                 })
#                     else:
#                         temp_list.append({
#                             'id': location.id,
#                             'distance': distance
#                         })
#                 print('unsorted', temp_list)
#                 if len(actual_locations) == 0:
#                     not_found = True
#                     sorted_cards = sorted(temp_list, key=lambda o: o['distance'])
#                     print('before:', list_of_ids)
#                     print('before', list_of_distance)
#                     print('sorted : ', sorted_cards)
#                     for i in range(3):
#                         list_of_ids.append(sorted_cards[i]['id'])
#                         list_of_distance.append(sorted_cards[i]['distance'])
#                         x = Location.objects.get(pk=sorted_cards[i]['id'])
#                         temp_locations.append(x)


#             else:
#                 print(obj.first_name)
#                 print(data)

#                 list_of_ids.append(obj.id)
#                 print('its the provider')
#         print(list_of_ids)


#     except:
#         messages.error(request, 'Please enter the correct specialty along with address!')

#     if not_found:
#         locations = temp_locations

#     else:

#         sorted_cards = sorted(actual_locations, key=lambda o: o['distance'])
#         for i in range(len(sorted_cards)):
#             print('this is the list ----')
#             list_of_ids.append(sorted_cards[i]['id'])
#             list_of_distance.append(sorted_cards[i]['distance'])
#         # for x in favorite_locations:
#         #     for _id in list_of_ids:
#         #         if x["location"].id == _id:
#         #             list_of_ids.remove(_id)
#         locations = Location.objects.filter(id__in=list_of_ids)

#     if check == False:
#         locations = Location.objects.filter(added_by=obj)
#     specialties = Specialty.objects.all()
#     favorite_locations = sorted(favorite_locations, key=lambda o: o['distance'])
#     print(locations)
#     print(list_of_distance)
#     context = {
#         'specialties': specialties,
#         'locations': locations,
#         'obj': obj,
#         'check': check,
#         'list_of_distance': list_of_distance,
#         'favorite_locations': favorite_locations
#     }
#     return render(request, 'accounts/filters.html', context)

def deletemultipleuser(request, user_id):
    user = User.objects.get(pk=user_id)
    profile = Firm.objects.get(user=request.user)
    try:
        if profile.account_type == 'Marketer':
            userprofile = Marketer.objects.get(marketerprofile=profile)
            xuser = MarketerStaff.objects.get(user=user)
        elif profile.account_type == 'Attorney':
            userprofile = Attorney.objects.get(attorneyprofile=profile)
            xuser = AttorneyStaff.objects.get(user=user)
        elif profile.account_type == 'Provider':
            userprofile = Provider.objects.get(providerprofile=profile)
            xuser = ProviderStaff.objects.get(user=user)

        xuser.delete()
        user.delete()
        messages.success(request, 'User has been deleted successfully!')
    except:
        messages.error(request, 'Operation Failed! Please try again.')

    if profile.account_type == 'Marketer':
        return redirect('marketer_firm_users')
    elif profile.account_type == 'Attorney':
        return redirect('firm_users')
    elif profile.account_type == 'Provider':
        return redirect('provider_firm_users')

    return render(request, 'accounts/firm_users.html')



def editmultipleuser(request, user_id):
    profile = Firm.objects.get(user=request.user)
    if profile.account_type == 'Marketer':
        userprofile = Marketer.objects.get(marketerprofile=profile)
    elif profile.account_type == 'Attorney':
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    elif profile.account_type == 'Provider':
        userprofile = Provider.objects.get(providerprofile=profile)
    user = User.objects.get(pk=user_id)
    if request.method == 'POST':
        try:

            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            permission = request.POST.get('permission')
            if permission == 'Yes':
                providerStaff = ProviderStaff.objects.get(user=user)
                providerStaff.permission = 'Yes'
                providerStaff.save()
            elif permission == 'No':
                providerStaff = ProviderStaff.objects.get(user=user)
                providerStaff.permission = 'No'
                providerStaff.save()
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            messages.success(request, 'User has been updated successfully!')
        except:
            messages.error(request, 'Operation Failed! Please try again.')

    context = {
        'userprofile': userprofile,
        'user':user,
    }
    return render(request, 'accounts/editmultipleusers.html', context)

def provider_firm_users(request):
    check = False
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)

    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        check = True

    if check:
        multipleusers = ProviderStaff.objects.filter(created_by=userprofile.created_by)
        userprofile = userprofile.created_by
    else:
        multipleusers = ProviderStaff.objects.filter(created_by=userprofile)

    context = {
        'multipleusers': multipleusers,
        'userprofile': userprofile
    }

    return render(request, 'accounts/firm_users.html', context)

def filters(request):
    name = ''
    list_of_ids = []
    temp_list = []
    obj = None
    check = False
    actual_locations = []
    not_found = False
    favorite_locations = []
    favorites = None
    actual_provider_locations = []
    profile = None
    index = 1
    userprofile = None
    blacklist_users = None
    flagged_users = None
    city = ''
    state = ''
    postal_code = ''
    country = ''
    speciality = ''
    isAttorney = False
    if request.user.is_authenticated:
        try:
            profile = Firm.objects.get(user=request.user)
            if profile.account_type == 'Marketer':
                userprofile = Marketer.objects.get(marketerprofile=profile)
            elif profile.account_type == 'Attorney':
                userprofile = Attorney.objects.get(attorneyprofile=profile)
                isAttorney = True
        except:
            try:
                userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
            except:
                userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
                isAttorney = True
            userprofile = userprofile.created_by

        if isAttorney:
            favorites = userprofile.favorites.all()
            blacklist_users = userprofile.blacklist.all()
            flagged_users = userprofile.flag.all()
    try:
        if request.method == 'POST':
            name = request.POST.get('name')

            data = name.split() #split string into a list
            obj = None
            print(data)
            for temp in data:
                try:
                    obj = Specialty.objects.get(name__icontains=temp)
                    if obj:
                        data.remove(temp)
                        check = True
                        break
                except:
                    try:
                        print('ahaha')
                        obj = Provider.objects.get(providerprofile__office_name__iexact=temp)
                        print(obj)
                        if obj:

                            data.remove(temp)
                            break
                    except:
                        pass

            input_address = ''
            for elem in data:
                input_address += elem
                input_address += ' '

            api_key = 'AIzaSyBqxc6kyS-LoyaHvVca125NQMefYWI3bn8'
            gmaps_client = googlemaps.Client(api_key)
            geocode_result = gmaps_client.geocode(input_address)
            result = geocode_result[0]

            input_latitude = result['geometry']['location']['lat']
            input_longitude = result['geometry']['location']['lng']


            print(input_latitude, input_longitude)

            address_components = result['address_components']

            def addressByType(type):
                filtered = list(filter(lambda x: type in x['types'], address_components))
                print(type, filtered)
                return filtered[0] if len(filtered) else {'long_name': '', 'short_name': ''}

            city = addressByType('locality')['long_name']
            state = addressByType('administrative_area_level_1')['short_name']
            postal_code = addressByType('postal_code')['long_name']
            country = addressByType('country')['long_name']


            if check:
                speciality = obj.name
                print(obj.name)
                print(data)
                print('its the specialty')
                locations = Location.objects.filter(specialties=obj)
                print(locations)
                for location in locations:
                    p = pi/180
                    a = 0.5 - cos((input_latitude-float(location.latitude))*p)/2 + cos(float(location.latitude)*p) * cos(input_latitude*p) * (1-cos((input_longitude-float(location.longitude))*p))/2
                    distance =  12742 * asin(sqrt(a)) #2*R*asin...
                    print(distance)
                    if distance <= obj.radius:
                        if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and isAttorney:
                            print('location', location.id)
                            check_temp = False
                            check_flag = False
                            for blacklist in blacklist_users:
                                if location.added_by.id == blacklist.id:
                                    check_temp = True
                            for flagged in flagged_users:
                                if location.added_by.id == flagged.provider.id:
                                    check_flag = True
                                    print('this is going')
                            if not check_temp:
                                try:
                                    fav_loc = favorites.get(provider=location.added_by, location=location, specialty=obj)
                                    if check_flag:
                                        favorite_locations.append({

                                            'provider': location.added_by,
                                            'obj': obj,
                                            'location': location,
                                            'distance':distance,
                                            'blacklist': False,
                                            'flagged':True,
                                        })
                                    else:
                                        favorite_locations.append({

                                            'provider': location.added_by,
                                            'obj': obj,
                                            'location': location,
                                            'distance':distance,
                                            'blacklist': False,
                                            'flagged':False,
                                        })
                                except:
                                    #list_of_ids.append(location.id)
                                    # print('this is location list -----', list_of_ids)
                                    # list_of_distance.append(distance)
                                    if check_flag:
                                        actual_locations.append({

                                            'provider': location.added_by,
                                            'obj': obj,
                                            'location': location,
                                            'distance': distance,
                                            'blacklist': False,
                                            'flagged':True
                                        })
                                    else:
                                        actual_locations.append({

                                            'provider': location.added_by,
                                            'obj': obj,
                                            'location': location,
                                            'distance': distance,
                                            'blacklist': False,
                                            'flagged':False
                                        })
                            else:
                                if check_flag:
                                    actual_locations.append({

                                            'provider': location.added_by,
                                            'obj': obj,
                                            'location': location,
                                            'distance': distance,
                                            'blacklist': True,
                                            'flagged': True
                                        })
                                else:
                                    actual_locations.append({

                                            'provider': location.added_by,
                                            'obj': obj,
                                            'location': location,
                                            'distance': distance,
                                            'blacklist': True,
                                            'flagged': False
                                        })
                        else:
                            actual_locations.append({

                                            'provider': location.added_by,
                                            'obj': obj,
                                            'location': location,
                                            'distance': distance,
                                            'blacklist': False,
                                            'flagged': False
                                        })
                    else:
                        if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and isAttorney:
                            check_temp = False
                            check_flag = False
                            for blacklist in blacklist_users:
                                if location.added_by.id == blacklist.id:
                                    check_temp = True
                            for flagged in flagged_users:
                                if location.added_by.id == flagged.provider.id:
                                    check_flag = True
                            if not check_temp:
                                if check_flag:
                                    temp_list.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance':distance,
                                        'blacklist': False,
                                        'flagged': True

                                    })
                                else:
                                    temp_list.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance':distance,
                                        'blacklist': False,
                                        'flagged': False

                                    })
                            else:
                                if check_flag:
                                    temp_list.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance':distance,
                                        'blacklist': True,
                                        'flagged': True,
                                    })
                                else:
                                    temp_list.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance':distance,
                                        'blacklist': True,
                                        'flagged': False
                                    })

                        else:
                            temp_list.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance':distance,
                                        'blacklist': False,
                                        'flagged': False
                                    })
                print('------------------------\n')
                print('unsorted', temp_list)

                if len(actual_locations) == 0:
                    print('ogogogogogogogg------')
                    not_found = True
                    temp_list = sorted(temp_list, key=lambda o: o['distance'])

                    # for i in range(3):
                    #     list_of_ids.append(sorted_cards[i]['id'])
                    #     list_of_distance.append(sorted_cards[i]['distance'])
                    #     x = Location.objects.get(pk=sorted_cards[i]['id'])
                    #     temp_locations.append(x)
                    temp_list = temp_list[:3]



            else:
                print(obj.first_name)
                print(data)

                list_of_ids.append(obj.id)
                print('its the provider')
        print(list_of_ids)


    except:
        messages.error(request, 'Please enter the correct specialty along with address!')

    if not_found:
        actual_locations = temp_list
        print('locations are', temp_list)
    else:

        actual_locations = sorted(actual_locations, key=lambda o: o['distance'])
        # for i in range(len(sorted_cards)):
        #     print('this is the list ----')
        #     list_of_ids.append(sorted_cards[i]['id'])
        #     list_of_distance.append(sorted_cards[i]['distance'])
        # for x in favorite_locations:
        #     for _id in list_of_ids:
        #         if x["location"].id == _id:
        #             list_of_ids.remove(_id)
        #locations = Location.objects.filter(id__in=list_of_ids)

    if check == False:
        locations = Location.objects.filter(added_by=obj)

        for location in locations:
            if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and isAttorney:
                for blacklist in blacklist_users:
                    if location.added_by.id == blacklist.id:
                        check_temp = True
                    if not check_temp:
                        temp_list.append({

                            'provider': location.added_by,
                            'obj': obj,
                            'location': location,
                            'distance':distance,
                            'blacklist': False,
                            'index':index
                        })
                        index = index + 1
                    else:
                        actual_provider_locations.append({
                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        })
            else:
                actual_provider_locations.append({
                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        })

    specialties = Specialty.objects.all()
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and isAttorney:
        favorite_locations = sorted(favorite_locations, key=lambda o: o['distance'])
        for favorite in favorite_locations:
                favorite['index'] = index
                index = index + 1
    for location in actual_locations:
        location['index'] = index
        index = index + 1
    if len(actual_locations) > 10:
        actual_locations = actual_locations[:10]
    context = {
        'specialties': specialties,
        'actual_locations': actual_locations,
        'obj': obj,
        'check': check,
        'actual_provider_locations': actual_provider_locations,
        'favorite_locations': favorite_locations,
        'name': name,
        'city': city,
        'state': state,
        'postal': postal_code,
        'country': country,
        'speciality': speciality
    }

    print('context', context)
    return render(request, 'accounts/filters.html', context)

def multipleusers(request):
    profile = Firm.objects.get(user=request.user)
    if profile.account_type == 'Attorney':
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    elif profile.account_type == 'Provider':
        userprofile = Provider.objects.get(providerprofile=profile)
    elif profile.account_type == 'Marketer':
        userprofile = Marketer.objects.get(marketerprofile=profile)

    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            hashed_pwd = make_password(password)

            user = User.objects.create(username=username, password=hashed_pwd, first_name=first_name, last_name=last_name, email=email)
            user.save()
            if profile.account_type == 'Attorney':
                staff = AttorneyStaff.objects.create(user=user, created_by=userprofile)
                staff.save()
            elif profile.account_type == 'Provider':
                staff = ProviderStaff.objects.create(user=user, created_by=userprofile)
                staff.save()
            elif profile.account_type == 'Marketer':
                staff = MarketerStaff.objects.create(user=user, created_by=userprofile)
                staff.save()

            messages.success(request, 'User has been added successfully!')
        except:
            messages.error(request, 'Operation Failed! Please try again.')

    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/multipleusers.html', context)

def addFlagged(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    try:
        profile = Firm.objects.get(user=request.user)
        if profile.account_type == 'Attorney':
            userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        description = request.POST.get('flag')
        flagged = Flagged.objects.create(provider=provider, description=description)
        flagged.save()
        userprofile.flag.add(flagged)
        userprofile.save()
        messages.warning(request, 'This Provider has been marked as Flagged!')

    return redirect('provider', provider.providerprofile.office_name)

def addBlacklist(request, provider_id):
    print('I ma on')
    provider = Provider.objects.get(pk=provider_id)
    reviews = Review.objects.filter(given_to=provider)
    # if profile.account_type == 'Marketer':
    #     userprofile = Marketer.objects.get(marketerprofile=profile)
    try:
        profile = Firm.objects.get(user=request.user)
        if profile.account_type == 'Attorney':
            userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    temp_rat = []
    for x in reviews:
        temp_rat.append((x.rating*100)/5)
    if request.method == 'POST':

        try:
            try:
                    userprofile.blacklist.remove(provider)
                    print('hello')
            except:
                pass
            provider_id = request.POST.get('blacklists')
            list_of_providers = Provider.objects.filter(pk=provider_id)
            for x in list_of_providers:
                try:
                    favorites = Favorite.objects.filter(provider=x)
                    for favorite in userprofile.favorites.all():
                        if favorite in favorites:
                            userprofile.favorites.remove(favorite)
                            userprofile.save()
                except:
                    pass
                userprofile.blacklist.add(x)
                print('Inside')
            userprofile.save()
            messages.success(request, 'Your Blacklist has been updated!')
        except:
            messages.error(request, 'Operation Failed! Try Again')

    return redirect('provider', provider.providerprofile.office_name)

def removeFavorite(request, favorite_id):
    check = False
    profile = None
    try:
        profile = Firm.objects.get(user=request.user)
        if profile.account_type == 'Marketer':
            userprofile = Marketer.objects.get(marketerprofile=profile)
            check = True
        elif profile.account_type == 'Attorney':
            userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        try:
            userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
            profile = userprofile.created_by.marketerprofile
            check = True
        except:
            userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
            profile = userprofile.created_by.attorneyprofile
        userprofile = userprofile.created_by

    try:
        favorite = Favorite.objects.get(pk=favorite_id)
        userprofile.favorites.remove(favorite)
        userprofile.save()

        if check:
            attorneys= Attorney.objects.filter(marketer_code=userprofile.marketer_code)
            # mark_favorites = userprofile.favorites.all()
            # for attorney in attorneys:
            #     existing_favorites = attorney.favorites.all()
            #     for mark_favorite in mark_favorites:
            #         if mark_favorite not in existing_favorites:
            #             attorney.favorites.add(mark_favorite)
            #             attorney.save()
            print(attorneys)
            for attorney in attorneys:
                favorites = attorney.favorites.all()
                if favorite in favorites:
                    attorney.favorites.remove(favorite)
        messages.success(request, 'Favorite has been removed from the list!')

    except:
        messages.error(request, 'Operation Failed! Please try Again')

    if profile.account_type == 'Attorney':
        return redirect('attorney_profile')
    elif profile.account_type == 'Marketer':
        return redirect('marketer_profile')

    context = {
        'userprofile': userprofile,
    }

    return render(request, 'accounts/profile.html', context)

# def removeFavorite(request, favorite_id):
#     checktemp = False
#     check=False
#     profile = None
#     try:
#         profile = Firm.objects.get(user=request.user)
#         if profile.account_type == 'Marketer':
#             userprofile = Marketer.objects.get(marketerprofile=profile)
#         elif profile.account_type == 'Attorney':
#             userprofile = Attorney.objects.get(attorneyprofile=profile)
#     except:
#         try:
#             userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
#         except:
#             userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
#         check=True

#     try:
#         favorite = Favorite.objects.get(pk=favorite_id)
#         if check:
#             userprofile.created_by.favorites.remove(favorite)
#             userprofile.save()
#         else:
#             userprofile.favorites.remove(favorite)
#             userprofile.save()

#         if checktemp:
#             if check:
#                 attorneys= Attorney.objects.filter(marketer_code=userprofile.created_by.marketer_code)
#             else:
#                 attorneys= Attorney.objects.filter(marketer_code=userprofile.marketer_code)
#             # mark_favorites = userprofile.favorites.all()
#             # for attorney in attorneys:
#             #     existing_favorites = attorney.favorites.all()
#             #     for mark_favorite in mark_favorites:
#             #         if mark_favorite not in existing_favorites:
#             #             attorney.favorites.add(mark_favorite)
#             #             attorney.save()

#             for attorney in attorneys:
#                 favorites = attorney.favorites.all()
#                 if favorite in favorites:
#                     attorney.favorites.remove(favorite)
#         messages.success(request, 'Favorite has been removed from the list!')

#     except:
#         messages.error(request, 'Operation Failed! Please try Again')

#     if not check:
#         if profile.account_type == 'Attorney':
#             return redirect('attorney_profile')
#         elif profile.account_type == 'Marketer':
#             return redirect('marketer_profile')
#     if check:
#         if userprofile.account_type == 'AttorneyStaff':
#             return redirect('attorney_profile')
#         elif userprofile.account_type == 'MarketerStaff':
#             return redirect('marketer_profile')

#     context = {
#         'userprofile': userprofile,
#     }

#     return render(request, 'accounts/profile.html', context)

def addFavorite(request, provider_id, location_id, specialty_id):

    provider = Provider.objects.get(pk=provider_id)
    specialty = Specialty.objects.get(pk=specialty_id)
    location = Location.objects.get(pk=location_id)
    check=False
    checktemp = False
    profile = None
    try:
        profile = Firm.objects.get(user=request.user)
        if profile.account_type == 'Marketer':
            userprofile = Marketer.objects.get(marketerprofile=profile)
            check = True
        elif profile.account_type == 'Attorney':
            userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        try:
            userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
            check = True
            profile = userprofile.created_by.marketerprofile
        except:
            userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
            profile = userprofile.created_by.attorneyprofile
        userprofile = userprofile.created_by

    try:

        favorite = Favorite.objects.create(provider=provider, location=location, specialty=specialty)
        favorite.save()
        userprofile.favorites.add(favorite)
        userprofile.save()
        if check:
            attorneys= Attorney.objects.filter(marketer_code=userprofile.marketer_code)
            # mark_favorites = userprofile.favorites.all()
            # for attorney in attorneys:
            #     existing_favorites = attorney.favorites.all()
            #     for mark_favorite in mark_favorites:
            #         if mark_favorite not in existing_favorites:
            #             attorney.favorites.add(mark_favorite)
            #             attorney.save()

            for attorney in attorneys:
                favorites = attorney.favorites.all()
                blacklists_users = attorney.blacklist.all()
                flagged_users = attorney.flag.all()
                if favorite not in favorites:
                    attorney.favorites.add(favorite)
                    if favorite.provider in blacklists_users:
                        attorney.blacklist.remove(favorite.provider)
                        attorney.save()
                    for xflag in flagged_users:
                        if favorite.provider.id == xflag.provider.id:
                            attorney.flag.remove(xflag)
                            attorney.save()
        else:
            blacklists_users = userprofile.blacklist.all()
            flagged_users = userprofile.flag.all()
            if favorite.provider in blacklists_users:
                userprofile.blacklist.remove(favorite.provider)
                userprofile.save()
            for xflag in flagged_users:
                if favorite.provider.id == xflag.provider.id:
                    userprofile.flag.remove(xflag)
                    userprofile.save()
        messages.success(request, 'Provider has been added to the List!')
    except:

        messages.error(request, 'Operation Failed! Please try Again')


    if profile.account_type == 'Attorney':
        return redirect('attorney_profile')
    elif profile.account_type == 'Marketer':
        return redirect('marketer_profile')


    context = {
        'userprofile': userprofile,
    }

    return render(request, 'accounts/profile.html', context)

# def addFavorite(request, provider_id, location_id, specialty_id):
#     provider = Provider.objects.get(pk=provider_id)
#     specialty = Specialty.objects.get(pk=specialty_id)
#     location = Location.objects.get(pk=location_id)
#     checktemp = False
#     check=False
#     profile = None
#     try:
#         profile = Firm.objects.get(user=request.user)
#         if profile.account_type == 'Marketer':
#             userprofile = Marketer.objects.get(marketerprofile=profile)
#         elif profile.account_type == 'Attorney':
#             userprofile = Attorney.objects.get(attorneyprofile=profile)
#     except:
#         try:
#             userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
#         except:
#             userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
#         check=True

#     try:

#         favorite = Favorite.objects.create(provider=provider, location=location, specialty=specialty)
#         favorite.save()
#         if check:
#             userprofile.created_by.favorites.add(favorite)
#             userprofile.created_by.save()
#         else:
#             userprofile.favorites.add(favorite)
#             userprofile.save()
#         if checktemp:
#             if check:
#                 attorneys= Attorney.objects.filter(marketer_code=userprofile.created_by.marketer_code)
#             else:
#                 attorneys= Attorney.objects.filter(marketer_code=userprofile.marketer_code)
#             # mark_favorites = userprofile.favorites.all()
#             # for attorney in attorneys:
#             #     existing_favorites = attorney.favorites.all()
#             #     for mark_favorite in mark_favorites:
#             #         if mark_favorite not in existing_favorites:
#             #             attorney.favorites.add(mark_favorite)
#             #             attorney.save()

#             for attorney in attorneys:
#                 favorites = attorney.favorites.all()
#                 if favorite not in favorites:
#                     attorney.favorites.add(favorite)

#         messages.success(request, 'Provider has been added to the List!')

#     except:
#         messages.error(request, 'Operation Failed! Please try Again')
#     if not check:
#         if profile.account_type == 'Attorney':
#             return redirect('attorney_profile')
#         elif profile.account_type == 'Marketer':
#             return redirect('marketer_profile')
#     if check:
#         if userprofile.account_type == 'AttorneyStaff':
#             return redirect('attorney_profile')
#         elif userprofile.account_type == 'MarketerStaff':
#             return redirect('marketer_profile')

#     context = {
#         'userprofile': userprofile,
#     }

#     return render(request, 'accounts/profile.html', context)


# def provider(request, office_name):
#     data = dict()
#     profile = Firm.objects.get(office_name=office_name, account_type='Provider')
#     provider = Provider.objects.get(providerprofile=profile)
#     reviews = Review.objects.filter(given_to=provider)
#     xprofile = Firm.objects.get(user=request.user)
#     temp_provider = []
#     provider_flags = None
#     userprofile = None
#     if xprofile.account_type == 'Marketer':
#         userprofile = Marketer.objects.get(marketerprofile=xprofile)
#     elif xprofile.account_type == 'Attorney':
#         userprofile = Attorney.objects.get(attorneyprofile=xprofile)
#         for x in userprofile.flag.all():
#             temp_provider.append(x.provider)
#         provider_flags = Flagged.objects.filter(provider=provider)
#     temp_rat = []
#     for x in reviews:
#         temp_rat.append((x.rating*100)/5)

#     if request.method == "POST":
#         rating = request.POST.get('rating')
#         x_profile = Firm.objects.get(user=request.user, account_type='Attorney')
#         attorney = Attorney.objects.get(attorneyprofile=x_profile)
#         description = request.POST.get('description')
#         post_as = request.POST.get('anonymous')

#         review = Review.objects.create(given_by=attorney, given_to=provider, rating=rating, description=description, post_as=post_as)
#         review.save()
#         sum = 0

#         print(reviews)
#         for x in reviews:
#             sum += float(x.rating)
#         count = Review.objects.filter(given_to=provider).count()
#         total = 5 * count
#         sum = int((sum*100)/total)
#         provider.review_percentage = sum
#         provider.save()
#         messages.success(request, 'Your review has been posted!')
#     print(userprofile)
#     context = {
#         'data': data,
#         'provider': provider,
#         'reviews':reviews,
#         'temp_rat': temp_rat,
#         'userprofile': userprofile,
#         'temp_provider': temp_provider,
#         'provider_flags': provider_flags
#     }
#     return render(request, 'accounts/provider.html', context)

def marketer_profile(request):
    try:
        profile = Firm.objects.get(user=request.user)
        if profile.account_type == 'Marketer':
            userprofile = Marketer.objects.get(marketerprofile=profile)
        # elif profile.account_type == 'Attorney':
        #     userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        userprofile = userprofile.created_by
    context = {

        'userprofile': userprofile
    }

    return render(request, 'accounts/profile.html', context)

def favorites(request):
    data = dict()
    specialties = Specialty.objects.all()
    providers = None
    check=False
    profile = None
    try:
        profile = Firm.objects.get(user=request.user)
        if profile.account_type == 'Marketer':
            userprofile = Marketer.objects.get(marketerprofile=profile)
        elif profile.account_type == 'Attorney':
            userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        try:

            userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        except:

            userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        check=True

    temp = []
    favorites = None
    if request.method == 'POST':

        name = request.POST.get('name')
        providers = Provider.objects.filter(providerprofile__office_name__icontains=name)
        if check:
            favorites = userprofile.created_by.favorites.all()
        else:
            favorites = userprofile.favorites.all()
        for provider in providers:
            locations = Location.objects.filter(added_by=provider)
            for location in locations:
                specialties = location.specialties.all()
                for specialty in specialties:
                    try:

                        x = favorites.get(provider=provider, location=location, specialty=specialty)


                    except:
                        temp.append({
                            'provider': provider,
                            'location': location,
                            'specialty': specialty
                        })


        print(providers)
        print(temp)



    context = {
        'userprofile':userprofile,
        'providers':providers,
        'data':data,
        'specialties': specialties,
        'temp': temp,
        'check':check
    }
    return render(request, 'accounts/favorites.html', context)


def marketer_code(request, attorney_id):
    userprofile = Attorney.objects.get(pk=attorney_id)
    if request.method == 'POST':
        marketer_code = request.POST.get('marketer_code')
        marketer = Marketer.objects.get(marketer_code=marketer_code)
        userprofile.marketer_code = marketer_code
        userprofile.save()
        favorites = marketer.favorites.all()
        existing_fav = userprofile.favorites.all()
        print(marketer)
        print(favorites)
        for favorite in favorites:
            if favorite not in existing_fav:
                userprofile.favorites.add(favorite)
                userprofile.save()
        print(userprofile)
        messages.success(request, 'Marketer Favorites are added to your list!')
    context = {
        'userprofile': userprofile
    }
    return redirect('attorney_profile')


def attorney_profile(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
        favorites = userprofile.favorites.all()
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        favorites = userprofile.created_by.favorites.all()
    context = {

        'userprofile': userprofile,
        'favorites': favorites
    }

    return render(request, 'accounts/profile.html', context)

def profile(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
        locations = Location.objects.filter(added_by=userprofile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        locations = Location.objects.filter(added_by=userprofile.created_by)

    context = {
        'locations':locations,
        'userprofile': userprofile
    }

    return render(request, 'accounts/profile.html', context)


def adddoctors(request):
    data = dict()
    check = False
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
        locations = Location.objects.filter(added_by=userprofile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        locations = Location.objects.filter(added_by=userprofile.created_by)
        check = True
    specialties = Specialty.objects.all()

    if request.method == 'POST':
        print("hello -----------")
        first_name1 = request.POST.get('first_name1')
        last_name1 = request.POST.get('last_name1')
        location1 = int(request.POST.get('location1'))
        location1 = Location.objects.get(pk=location1)
        specialties = request.POST.getlist('specialties')
        specialties = [int(i) for i in specialties]
        try:

            if check:
                doctor = Doctor.objects.create(created_by=userprofile.created_by, first_name=first_name1, last_name=last_name1,
                            location=location1
                            )
            else:
                doctor = Doctor.objects.create(created_by=userprofile, first_name=first_name1, last_name=last_name1,
                            location=location1
                            )
            for specialty in specialties:
                obj = Specialty.objects.get(pk=specialty)
                doctor.specialties.add(obj)
            doctor.save()
            messages.success(request, "Doctor has been added successfully!")
        except:
            messages.error(request, "Doctor cannot be added. Please try Again!")
    context = {
        'data':data,
        'specialties': specialties,
        'locations': locations
    }
    return render(request, 'accounts/adddoctors.html', context)

def marketerlocation(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Marketer')
        userprofile = Marketer.objects.get(marketerprofile=profile)
    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        print("hello -----------")
        address1 = request.POST.get('address1')
        city1 = request.POST.get('city1')
        state1 = request.POST.get('state1')
        country1 = request.POST.get('country1')
        address3 = request.POST.get('address3')
        postal1 = request.POST.get('postal1')
        email1 = request.POST.get('email1')
        phone1 = request.POST.get('phone1')
        fax1 = request.POST.get('fax1')
        try:
            location = MarketerLocation.objects.create(added_by=userprofile, address=address1, city=city1,
                    state=state1, country=country1, post_code=postal1, address2=address3, fax=fax1, email=email1,
                    phone=phone1
                    )
            location.save()
            messages.success(request, 'Address has been added successfully!')
        except:
            messages.error(request, "Address can't be added right now. Please try again")
    context = {
        'userprofile':userprofile,
    }
    return render(request, 'accounts/attorneylocation.html', context)

def attorneylocation(request):
    try:
        check = False
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        check = True
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')

    if request.method == 'POST':
        print("hello -----------")
        address1 = request.POST.get('address1')
        city1 = request.POST.get('city1')
        state1 = request.POST.get('state1')
        country1 = request.POST.get('country1')
        address3 = request.POST.get('address3')
        postal1 = request.POST.get('postal1')
        email1 = request.POST.get('email1')
        phone1 = request.POST.get('phone1')
        fax1 = request.POST.get('fax1')
        try:
            if check:

                location = AttorneyLocation.objects.create(added_by=userprofile.created_by, address=address1, city=city1,
                        state=state1, country=country1, post_code=postal1, address2=address3, fax=fax1, email=email1,
                        phone=phone1
                        )
                location.save()
            else:
                location = AttorneyLocation.objects.create(added_by=userprofile, address=address1, city=city1,
                        state=state1, country=country1, post_code=postal1, address2=address3, fax=fax1, email=email1,
                        phone=phone1
                        )
                location.save()
            messages.success(request, 'Address has been added successfully!')
        except:
            messages.error(request, "Address can't be added right now. Please try again")
    context = {
        'userprofile':userprofile,
        'check':check
    }
    return render(request, 'accounts/attorneylocation.html', context)


def addlocations(request, check=False):
    data = dict()
    specialties = Specialty.objects.all()
    if request.method == 'POST':
        print("hello -----------")
        address1 = request.POST.get('address1')
        city1 = request.POST.get('city1')
        state1 = request.POST.get('state1')
        country1 = request.POST.get('country1')
        address3 = request.POST.get('address3')
        postal1 = request.POST.get('postal1')
        longitude1 = request.POST.get('longitude1')
        latitude1 = request.POST.get('latitude1')
        phone1 = request.POST.get('phone1')
        fax1 = request.POST.get('fax1')
        email1 = request.POST.get('email1')
        specialties = request.POST.getlist('specialties')
        specialties = [int(i) for i in specialties]

        value = request.POST.get('value')
        if value == 'True':
            check=True

        bill_request_address1 = request.POST.get('bill-request-address1')
        bill_request_address2 = request.POST.get('bill-request-address2')
        bill_request_city = request.POST.get('bill-request-city')
        bill_request_state = request.POST.get('bill-request-state')
        bill_request_zip = request.POST.get('bill-request-zip')

        bill_request_phone = request.POST.get('bill-request-phone')
        bill_request_fax = request.POST.get('bill-request-fax')
        bill_request_type = 'Billing Request Contact'
        bill_request_email = request.POST.get('bill-request-email')


        record_request_address1 = request.POST.get('record-request-address1')
        record_request_address2 = request.POST.get('record-request-address2')
        record_request_city = request.POST.get('record-request-city')
        record_request_state = request.POST.get('record-request-state')
        record_request_zip = request.POST.get('record-request-zip')
        
        record_request_phone = request.POST.get('record-request-phone')
        record_request_fax = request.POST.get('record-request-fax')
        record_request_type = 'Records Request Contact'
        record_request_email = request.POST.get('record-request-email')



        bill_payment_request_address1 = request.POST.get('bill-payment-request-address1')
        bill_payment_request_address2 = request.POST.get('bill-payment-request-address2')
        bill_payment_request_city = request.POST.get('bill-payment-request-city')
        bill_payment_request_state = request.POST.get('bill-payment-request-state')
        bill_payment_request_zip = request.POST.get('bill-payment-request-zip')
        bill_payment_request_phone = request.POST.get('bill-payment-request-phone')
        bill_payment_request_fax = request.POST.get('bill-payment-request-fax')
        bill_payment_request_type = 'Billing Request Payment'
        bill_payment_request_email = request.POST.get('bill-payment-request-email')

        record_payment_request_address1 = request.POST.get('record-payment-request-address1')
        record_payment_request_address2 = request.POST.get('record-payment-request-address2')
        record_payment_request_city = request.POST.get('record-payment-request-city')
        record_payment_request_state = request.POST.get('record-payment-request-state')
        record_payment_request_zip = request.POST.get('record-payment-request-zip')
        
        record_payment_request_phone = request.POST.get('record-payment-request-phone')
        record_payment_request_fax = request.POST.get('record-payment-request-fax')
        record_payment_request_type = 'Records Request Payment'
        record_payment_request_email = request.POST.get('record-payment-request-email')



        try:

            try:
                profile = Firm.objects.get(user=request.user, account_type='Provider')
                userprofile = Provider.objects.get(providerprofile=profile)
                location = Location.objects.create(added_by=userprofile,address=address1,address2=address3, city=city1, state=state1, country=country1, post_code=postal1,
                        longitude=longitude1, latitude=latitude1, fax=fax1, phone=phone1, email=email1
                        )
            except:
                userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
                location = Location.objects.create(added_by=userprofile.created_by,address=address1,address2=address3, city=city1, state=state1, country=country1, post_code=postal1,
                        longitude=longitude1, latitude=latitude1, fax=fax1, phone=phone1, email=email1
                        )
                userprofile = userprofile.created_by

            for specialty in specialties:
                obj = Specialty.objects.get(pk=specialty)
                location.specialties.add(obj)
            location.save()
            temp_check = False
            
            if OtherLocations.objects.filter(for_provider=userprofile).count() > 0:
                print('hahahahhaha')
                temp_check = True
            
            
            if not temp_check:
            
                bill_request_location = OtherLocations.objects.create(for_provider=userprofile, 
                                        phone=bill_request_phone, fax=bill_request_fax, email=bill_request_email,
                                        address_type=bill_request_type,
                                        address=bill_request_address1,
                                        address2=bill_request_address2,
                                        city=bill_request_city,
                                        state=bill_request_state,
                                        post_code=bill_request_zip
                                        )
                bill_request_location.save()

                record_request_location = OtherLocations.objects.create(for_provider=userprofile,
                                        phone=record_request_phone, fax=record_request_fax, email=record_request_email,
                                        address_type=record_request_type,
                                        address=record_request_address1,
                                        address2=record_request_address2,
                                        city=record_request_city,
                                        state=record_request_state,
                                        post_code=record_request_zip
                                        )
                record_request_location.save()

                bill_payment_request_location = OtherLocations.objects.create(for_provider=userprofile, 
                                        phone=bill_payment_request_phone, fax=bill_payment_request_fax, email=bill_payment_request_email,
                                        address_type=bill_payment_request_type,
                                        address=bill_payment_request_address1,
                                        address2=bill_payment_request_address2,
                                        city=bill_payment_request_city,
                                        state=bill_payment_request_state,
                                        post_code=bill_payment_request_zip
                                        )
                bill_payment_request_location.save()

                record_payment_request_location = OtherLocations.objects.create(for_provider=userprofile, 
                                        phone=record_payment_request_phone, fax=record_payment_request_fax, email=record_payment_request_email,
                                        address_type=record_payment_request_type,
                                        address=record_payment_request_address1,
                                        address2=record_payment_request_address2,
                                        city=record_payment_request_city,
                                        state=record_payment_request_state,
                                        post_code=record_payment_request_zip
                                        )
                record_payment_request_location.save()
            messages.success(request, "Address has been added successfully!")
            if check:
                return redirect('addlocations')
            else:
                return redirect('profile')
        except:
            messages.error(request, "Address cannot be added. Please try Again!")

    context = {
        'google_api_key': settings.GOOGLE_API_KEY,
        'data': data,
        'specialties':specialties,
    }

    return render(request, 'accounts/addlocations.html', context)

def editlocations(request, location_id, provider_id):
    data = dict()
    specialties = Specialty.objects.all()
    provider = Provider.objects.get(pk=provider_id)
    location = Location.objects.get(pk=location_id)
    # bill_request_location = OtherLocations.objects.get(for_provider=provider, address_type='Medical Bill Request Location')
    # record_request_location = OtherLocations.objects.get(for_provider=provider, address_type='Medical Record Request Location')
    # bill_payment_request_location = OtherLocations.objects.get(for_provider=provider, address_type='Medical Bill Request Payment Location')
    # record_payment_request_location = OtherLocations.objects.get(for_provider=provider, address_type='Medical Record Request Payment Location')

    if request.method == 'POST':
        print("hello -----------")
        address1 = request.POST.get('address1')
        city1 = request.POST.get('city1')
        state1 = request.POST.get('state1')
        country1 = request.POST.get('country1')
        address3 = request.POST.get('address3')
        postal1 = request.POST.get('postal1')
        longitude1 = request.POST.get('longitude1')
        latitude1 = request.POST.get('latitude1')
        phone1 = request.POST.get('phone1')
        fax1 = request.POST.get('fax1')
        email1 = request.POST.get('email1')
        specialties = request.POST.getlist('specialties')
        specialties = [int(i) for i in specialties]

        print(specialties)

        # bill_request_address = request.POST.get('bill-request-address')
        # bill_request_phone = request.POST.get('bill-request-phone')
        # bill_request_fax = request.POST.get('bill-request-fax')
        # bill_request_type = 'Medical Bill Request Location'
        # bill_request_email = request.POST.get('bill-request-email')

        # record_request_address = request.POST.get('record-request-address')
        # record_request_phone = request.POST.get('record-request-phone')
        # record_request_fax = request.POST.get('record-request-fax')
        # record_request_type = 'Medical Record Request Location'
        # record_request_email = request.POST.get('record-request-email')

        # bill_payment_request_address = request.POST.get('bill-payment-request-address')
        # bill_payment_request_phone = request.POST.get('bill-payment-request-phone')
        # bill_payment_request_fax = request.POST.get('bill-payment-request-fax')
        # bill_payment_request_type = 'Medical Bill Request Payment Location'
        # bill_payment_request_email = request.POST.get('bill-payment-request-email')

        # record_payment_request_address = request.POST.get('record-payment-request-address')
        # record_payment_request_phone = request.POST.get('record-payment-request-phone')
        # record_payment_request_fax = request.POST.get('record-payment-request-fax')
        # record_payment_request_type = 'Medical Record Request Payment Location'
        # record_payment_request_email = request.POST.get('record-payment-request-email')

        try:
            location.address = address1
            location.city = city1
            location.state = state1
            location.country = country1
            location.address2 = address3
            location.post_code = postal1
            location.longitude = longitude1
            location.latitude = latitude1
            location.fax = fax1
            location.phone = phone1
            location.email = email1
            location.specialties.clear()
            for specialty in specialties:
                obj = Specialty.objects.get(pk=specialty)
                location.specialties.add(obj)
            location.save()


            # bill_request_location.name = bill_request_address
            # bill_request_location.phone = bill_request_phone
            # bill_request_location.email = bill_request_email
            # bill_request_location.address_type = bill_request_type
            # bill_request_location.fax = bill_request_fax
            # bill_request_location.save()



            # record_request_location.name = record_request_address
            # record_request_location.phone = record_request_phone
            # record_request_location.email = record_request_email
            # record_request_location.address_type = record_request_type
            # record_request_location.fax = record_request_fax
            # record_request_location.save()



            # bill_payment_request_location.name = bill_payment_request_address
            # bill_payment_request_location.phone = bill_payment_request_phone
            # bill_payment_request_location.email = bill_payment_request_email
            # bill_payment_request_location.address_type = bill_payment_request_type
            # bill_payment_request_location.fax = bill_payment_request_fax
            # bill_payment_request_location.save()



            # record_payment_request_location.name = record_payment_request_address
            # record_payment_request_location.phone = record_payment_request_phone
            # record_payment_request_location.email = record_payment_request_email
            # record_payment_request_location.address_type = record_payment_request_type
            # record_payment_request_location.fax = record_payment_request_fax
            # record_payment_request_location.save()

            messages.success(request, "Address has been updated successfully!")
            if request.user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('profile')
        except:
            messages.error(request, "Address cannot be updated. Please try Again!")
            return redirect('profile')


    context = {
        'google_api_key': settings.GOOGLE_API_KEY,
        'data': data,
        'specialties':specialties,
        'location': location,
        'provider': provider,
        # 'bill_request_location': bill_request_location,
        # 'record_request_location': record_request_location,
        # 'bill_payment_request_location': bill_payment_request_location,
        # 'record_payment_request_location': record_payment_request_location
    }

    return render(request, 'accounts/editlocations.html', context)




def home(request):
    data = dict()
    specialties = Specialty.objects.all().order_by('name')
    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password1')
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:

            messages.error(request, "username or password is incorrect")

    context = {
        'specialties': specialties,
        'data': data
    }

    return render(request, 'accounts/index.html', context)

def marketer_firm_users(request):
    check = False
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Marketer')
        userprofile = Marketer.objects.get(marketerprofile=profile)

    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        check = True

    if check:
        multipleusers = MarketerStaff.objects.filter(created_by=userprofile.created_by)
        userprofile = userprofile.created_by
    else:
        multipleusers = MarketerStaff.objects.filter(created_by=userprofile)

    context = {
        'multipleusers': multipleusers,
        'userprofile': userprofile
    }

    return render(request, 'accounts/firm_users.html', context)

def marketer_blacklist(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Marketer')
        userprofile = Marketer.objects.get(marketerprofile=profile)
    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        userprofile = userprofile.created_by

    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/marketer_blacklist.html', context)

def marketer_provider_reviews(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Marketer')
        userprofile = Marketer.objects.get(marketerprofile=profile)
    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        userprofile = userprofile.created_by

    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/marketer_provider_reviews.html', context)


def firm_users(request):
    check = False
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)

    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        check = True

    if check:
        multipleusers = AttorneyStaff.objects.filter(created_by=userprofile.created_by)
        userprofile = userprofile.created_by
    else:
        multipleusers = AttorneyStaff.objects.filter(created_by=userprofile)

    context = {
        'multipleusers': multipleusers,
        'userprofile': userprofile
    }

    return render(request, 'accounts/firm_users.html', context)

def blacklist(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by

    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/blacklist.html', context)

def flagged_users(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/flagged_users.html', context)

def provider_reviews(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    reviews = Review.objects.filter(given_by=userprofile)
    temp_rat = []
    for x in reviews:
        temp_rat.append((x.rating*100)/5)
    context = {
        'userprofile': userprofile,
        'temp_rat': temp_rat,
        'reviews': reviews
    }
    return render(request, 'accounts/provider_reviews.html', context)



def accountdetails_marketer(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Marketer')
        userprofile = Marketer.objects.get(marketerprofile=profile)
    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        email = request.POST.get('email')
        user = request.user
        user.email = email
        user.save()
        messages.success(request, "Account details has been updated")
        return redirect('accountdetails_marketer')
    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/accountdetails.html', context)

def accountdetails_attorney(request):
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        email = request.POST.get('email')
        user = request.user
        user.email = email
        user.save()
        messages.success(request, "Account details has been updated")
        return redirect('accountdetails_attorney')
    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/accountdetails.html', context)

def accountdetails(request):
    check = False
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        check = True
    if request.method == 'POST':
        email = request.POST.get('email')
        user = request.user
        user.email = email
        user.save()
        messages.success(request, "Account details has been updated")
        return redirect('accountdetails')
    context = {
        'userprofile': userprofile,
        'check':check
    }
    return render(request, 'accounts/accountdetails.html', context)

def providerdetails(request):
    check = False
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)
    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        description = request.POST.get('description')
        website = request.POST.get('website')
        fb_page = request.POST.get('fb_page')
        twitter_page = request.POST.get('twitter_page')
        google_page = request.POST.get('google_page')

        userprofile.description = description
        userprofile.website = website
        userprofile.fb_page = fb_page
        userprofile.twitter_page = twitter_page
        userprofile.google_page = google_page
        userprofile.save()

        messages.success(request, "Provider details has been updated")
        return redirect('providerdetails')
    context = {
        'userprofile': userprofile
    }
    return render(request, 'accounts/providerdetails.html', context)

def aboutus(request):
    return render(request, 'accounts/aboutus.html')

def privacy(request):
    return render(request, 'accounts/privacy.html')

def contactus(request):
    return render(request, 'accounts/contactus.html')

def updateMarketerCode(request):
    data = dict()
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Marketer')
        userprofile = Marketer.objects.get(marketerprofile=profile)
    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        marketer_code = request.POST.get('marketer_code')
        userprofile.marketer_code = marketer_code
        userprofile.save()
        messages.success(request, 'Marketing Code has been updated!')

    context = {
        'userprofile': userprofile,
        'data': data,
    }
    return render(request, 'accounts/marketer.html', context)

def marketer(request):
    data = dict()
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Marketer')
        userprofile = Marketer.objects.get(marketerprofile=profile)
    except:
        userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        marketer_code = request.POST.get('marketer_code')

        userprofile.marketerprofile.first_name = first_name
        userprofile.marketerprofile.last_name = last_name
        userprofile.marketer_code = marketer_code
        userprofile.save()
        messages.success(request, 'Account details has been updated!')

    context = {
        'userprofile': userprofile,
        'data': data,
    }
    return render(request, 'accounts/marketer.html', context)

def attorneyInfo(request):
    return render(request, 'accounts/attorneyInfo.html')

def medicalProviders(request):
    return render(request, 'accounts/medicalProviders.html')

def marketerInfo(request):
    return render(request, 'accounts/marketerInfo.html')

def register(request, role):
    account_type = role
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = request.POST.get('email')
            user.save()
            first_name = request.POST.get('first_name')
            office_name = request.POST.get('office_name')
            last_name = request.POST.get('last_name')
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            # account_type = request.POST.get('account_type', 'Provider')
            userprofile = Firm.objects.create(user = user, office_name=office_name, first_name=first_name, last_name=last_name, account_type=account_type)
            userprofile.save()
            if account_type == 'Provider':
                provider = Provider.objects.create(providerprofile=userprofile)
                provider.save()
            elif account_type == 'Attorney':
                attorney = Attorney.objects.create(attorneyprofile=userprofile)
                attorney.save()
            elif account_type == 'Marketer':
                marketer = Marketer.objects.create(marketerprofile=userprofile)
                S = 15  # number of characters in the string.
                ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
                marketer.marketer_code = ran
                marketer.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form':form})


def loginPage(request):
    data = dict()
    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password1')
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:

            messages.error(request, "Username or password is incorrect")

    return render(request, 'accounts/login.html', data)

@login_required(login_url='home')
def logoutPage(request):
    logout(request)
    return redirect('home')

def advance_filters(request):
    list_of_ids = []
    temp_list = []
    list_of_distance = []
    obj = None
    check = True
    not_found = False
    temp_locations = []
    actual_locations = []
    favorite_locations = []
    favorites = None
    actual_provider_locations = []
    profile = None
    index = 1
    userprofile = None
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff:
        try:
            profile = Firm.objects.get(user=request.user)
            if profile.account_type == 'Attorney':
                userprofile = Attorney.objects.get(attorneyprofile=profile)
        except:
            userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
            userprofile = userprofile.created_by

        favorites = userprofile.favorites.all()
        blacklist_users = userprofile.blacklist.all()
        flagged_users = userprofile.flag.all()
    try:
        if request.method == "POST":
            specialty = request.POST.get('specialty', 'Chiropractor')
            address = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            postal = request.POST.get('postal')
            if specialty == 'Select Specialty':
                specialty = 'Chiropractor'
            input_address = str(address) + str(city) + str(state) + str(postal)
            print(input_address)

            obj = Specialty.objects.get(name__icontains=specialty)

            api_key = 'AIzaSyBqxc6kyS-LoyaHvVca125NQMefYWI3bn8'
            gmaps_client = googlemaps.Client(api_key)
            geocode_result = gmaps_client.geocode(input_address)
            result = geocode_result[0]

            input_latitude = result['geometry']['location']['lat']
            input_longitude = result['geometry']['location']['lng']


            print(input_latitude, input_longitude)

            print(obj.name)

            print('its the specialty')

            locations = Location.objects.filter(specialties=obj)
            print(locations)
            for location in locations:
                p = pi/180
                a = 0.5 - cos((input_latitude-float(location.latitude))*p)/2 + cos(float(location.latitude)*p) * cos(input_latitude*p) * (1-cos((input_longitude-float(location.longitude))*p))/2
                distance =  12742 * asin(sqrt(a)) #2*R*asin...
                print(distance)
                if distance <= obj.radius:
                    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff:
                        print('location', location.id)
                        check_temp = False
                        check_flag = False
                        for blacklist in blacklist_users:
                            if location.added_by.id == blacklist.id:
                                check_temp = True
                        for flagged in flagged_users:
                            if location.added_by.id == flagged.provider.id:
                                check_flag = True
                                print('this is going')
                        if not check_temp:
                            try:
                                fav_loc = favorites.get(provider=location.added_by, location=location, specialty=obj)
                                if check_flag:
                                    favorite_locations.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance':distance,
                                        'blacklist': False,
                                        'flagged':True,

                                    })

                                else:
                                    favorite_locations.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance':distance,
                                        'blacklist': False,
                                        'flagged':False,

                                    })

                            except:
                                #list_of_ids.append(location.id)
                                # print('this is location list -----', list_of_ids)
                                # list_of_distance.append(distance)
                                if check_flag:
                                    actual_locations.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance': distance,
                                        'blacklist': False,
                                        'flagged':True

                                    })
                                else:
                                    actual_locations.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance': distance,
                                        'blacklist': False,
                                        'flagged':False
                                    })
                        else:
                            if check_flag:
                                actual_locations.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance': distance,
                                        'blacklist': True,
                                        'flagged': True
                                    })
                            else:
                                actual_locations.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance': distance,
                                        'blacklist': True,
                                        'flagged': False
                                    })
                    else:
                        actual_locations.append({

                                        'provider': location.added_by,
                                        'obj': obj,
                                        'location': location,
                                        'distance': distance,
                                        'blacklist': False,
                                        'flagged': False

                                    })

                else:
                    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff:
                        check_temp = False
                        check_flag = False
                        for blacklist in blacklist_users:
                            if location.added_by.id == blacklist.id:
                                check_temp = True
                        for flagged in flagged_users:
                            if location.added_by.id == flagged.provider.id:
                                check_flag = True
                        if not check_temp:
                            if check_flag:
                                temp_list.append({

                                    'provider': location.added_by,
                                    'obj': obj,
                                    'location': location,
                                    'distance':distance,
                                    'blacklist': False,
                                    'flagged': True

                                })
                            else:
                                temp_list.append({

                                    'provider': location.added_by,
                                    'obj': obj,
                                    'location': location,
                                    'distance':distance,
                                    'blacklist': False,
                                    'flagged': False

                                })
                        else:
                            if check_flag:
                                temp_list.append({

                                    'provider': location.added_by,
                                    'obj': obj,
                                    'location': location,
                                    'distance':distance,
                                    'blacklist': True,
                                    'flagged': True,
                                })
                            else:
                                temp_list.append({

                                    'provider': location.added_by,
                                    'obj': obj,
                                    'location': location,
                                    'distance':distance,
                                    'blacklist': True,
                                    'flagged': False
                                })
                    else:
                        temp_list.append({

                                    'provider': location.added_by,
                                    'obj': obj,
                                    'location': location,
                                    'distance':distance,
                                    'blacklist': False,
                                    'flagged': False
                                })
            print('unsorted', temp_list)
            if len(actual_locations) == 0:
                not_found = True
                temp_list = sorted(temp_list, key=lambda o: o['distance'])

                # for i in range(3):
                #     list_of_ids.append(sorted_cards[i]['id'])
                #     list_of_distance.append(sorted_cards[i]['distance'])
                #     x = Location.objects.get(pk=sorted_cards[i]['id'])
                #     temp_locations.append(x)
                temp_list = temp_list[:3]
    except:
        messages.error(request, 'Please enter the correct specialty along with address!')

    if not_found:
        actual_locations = temp_list

    else:

        actual_locations = sorted(actual_locations, key=lambda o: o['distance'])
    specialties = Specialty.objects.all().order_by('name')
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff:
        favorite_locations = sorted(favorite_locations, key=lambda o: o['distance'])
        for favorite in favorite_locations:
            favorite['index'] = index
            index = index + 1
    for location in actual_locations:
        location['index'] = index
        index = index + 1

    context = {
        'specialties': specialties,
        'actual_locations': actual_locations,
        'obj': obj,
        'check': check,
        'actual_provider_locations': actual_provider_locations,
        'favorite_locations': favorite_locations,
        'address':address,
        'postal':postal,
        'city':city,
        'state':state
    }
    return render(request, 'accounts/filters.html', context)


# def advance_filters(request):
#     list_of_ids = []
#     temp_list = []
#     list_of_distance = []
#     obj = None
#     check = True
#     not_found = False
#     userprofile = None
#     temp_locations = []
#     actual_locations = []
#     favorite_locations = []
#     favorites = None
#     actual_provider_locations = []
#     profile = None
#     if request.user.is_authenticated:
#         try:
#             profile = Firm.objects.get(user=request.user)
#             if profile.account_type == 'Attorney':
#                 userprofile = Attorney.objects.get(attorneyprofile=profile)
#         except:
#             userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
#             userprofile = userprofile.created_by

#             favorites = userprofile.favorites.all()
#             blacklist_users = userprofile.blacklist.all()
#             flagged_users = userprofile.flag.all()
#     try:
#         if request.method == "POST":
#             specialty = request.POST.get('specialty')
#             address = request.POST.get('address')
#             city = request.POST.get('city')
#             state = request.POST.get('state')
#             postal = request.POST.get('postal')

#             input_address = str(address) + str(city) + str(state) + str(postal)
#             print(input_address)

#             obj = Specialty.objects.get(name__icontains=specialty)

#             api_key = 'AIzaSyBqxc6kyS-LoyaHvVca125NQMefYWI3bn8'
#             gmaps_client = googlemaps.Client(api_key)
#             geocode_result = gmaps_client.geocode(input_address)
#             result = geocode_result[0]

#             input_latitude = result['geometry']['location']['lat']
#             input_longitude = result['geometry']['location']['lng']


#             print(input_latitude, input_longitude)

#             print(obj.name)

#             print('its the specialty')

#             locations = Location.objects.filter(specialties=obj)
#             print(locations)
#             for location in locations:
#                 p = pi/180
#                 a = 0.5 - cos((input_latitude-float(location.latitude))*p)/2 + cos(float(location.latitude)*p) * cos(input_latitude*p) * (1-cos((input_longitude-float(location.longitude))*p))/2
#                 distance =  12742 * asin(sqrt(a)) #2*R*asin...
#                 print(distance)
#                 if distance <= obj.radius:
#                     print('location', location.id)
#                     if request.user.is_authenticated:
#                         check_temp = False
#                         check_flag = False
#                         for blacklist in blacklist_users:
#                             if location.added_by.id == blacklist.id:
#                                 check_temp = True
#                         for flagged in flagged_users:
#                             if location.added_by.id == flagged.provider.id:
#                                 check_flag = True
#                                 print('this is going')
#                         if not check_temp:
#                             try:
#                                 fav_loc = favorites.get(provider=location.added_by, location=location, specialty=obj)
#                                 if check_flag:
#                                     favorite_locations.append({

#                                         'provider': location.added_by,
#                                         'obj': obj,
#                                         'location': location,
#                                         'distance':distance,
#                                         'blacklist': False,
#                                         'flagged':True,
#                                     })
#                                 else:
#                                     favorite_locations.append({

#                                         'provider': location.added_by,
#                                         'obj': obj,
#                                         'location': location,
#                                         'distance':distance,
#                                         'blacklist': False,
#                                         'flagged':False,
#                                     })
#                             except:
#                                 #list_of_ids.append(location.id)
#                                 # print('this is location list -----', list_of_ids)
#                                 # list_of_distance.append(distance)
#                                 if check_flag:
#                                     actual_locations.append({

#                                         'provider': location.added_by,
#                                         'obj': obj,
#                                         'location': location,
#                                         'distance': distance,
#                                         'blacklist': False,
#                                         'flagged':True
#                                     })
#                                 else:
#                                     actual_locations.append({

#                                         'provider': location.added_by,
#                                         'obj': obj,
#                                         'location': location,
#                                         'distance': distance,
#                                         'blacklist': False,
#                                         'flagged':False
#                                     })
#                         else:
#                             if check_flag:
#                                 actual_locations.append({

#                                         'provider': location.added_by,
#                                         'obj': obj,
#                                         'location': location,
#                                         'distance': distance,
#                                         'blacklist': True,
#                                         'flagged': True
#                                     })
#                             else:
#                                 actual_locations.append({

#                                         'provider': location.added_by,
#                                         'obj': obj,
#                                         'location': location,
#                                         'distance': distance,
#                                         'blacklist': True,
#                                         'flagged': False
#                                     })
#                     else:
#                         actual_locations.append({

#                                         'provider': location.added_by,
#                                         'obj': obj,
#                                         'location': location,
#                                         'distance': distance,
#                                         'blacklist': False,
#                                         'flagged': False
#                                     })
#                 else:
#                     if request.user.is_authenticated:
#                         check_temp = False
#                         check_flag = False
#                         for blacklist in blacklist_users:
#                             if location.added_by.id == blacklist.id:
#                                 check_temp = True
#                         for flagged in flagged_users:
#                             if location.added_by.id == flagged.provider.id:
#                                 check_flag = True
#                         if not check_temp:
#                             if check_flag:
#                                 temp_list.append({

#                                     'provider': location.added_by,
#                                     'obj': obj,
#                                     'location': location,
#                                     'distance':distance,
#                                     'blacklist': False,
#                                     'flagged': True

#                                 })
#                             else:
#                                 temp_list.append({

#                                     'provider': location.added_by,
#                                     'obj': obj,
#                                     'location': location,
#                                     'distance':distance,
#                                     'blacklist': False,
#                                     'flagged': False

#                                 })
#                         else:
#                             if check_flag:
#                                 temp_list.append({

#                                     'provider': location.added_by,
#                                     'obj': obj,
#                                     'location': location,
#                                     'distance':distance,
#                                     'blacklist': True,
#                                     'flagged': True,
#                                 })
#                             else:
#                                 temp_list.append({

#                                     'provider': location.added_by,
#                                     'obj': obj,
#                                     'location': location,
#                                     'distance':distance,
#                                     'blacklist': True,
#                                     'flagged': False
#                                 })
#                     else:
#                         temp_list.append({

#                                     'provider': location.added_by,
#                                     'obj': obj,
#                                     'location': location,
#                                     'distance':distance,
#                                     'blacklist': False,
#                                     'flagged': False
#                                 })
#             print('unsorted', temp_list)
#             if len(actual_locations) == 0:
#                 not_found = True
#                 temp_list = sorted(temp_list, key=lambda o: o['distance'])

#                 # for i in range(3):
#                 #     list_of_ids.append(sorted_cards[i]['id'])
#                 #     list_of_distance.append(sorted_cards[i]['distance'])
#                 #     x = Location.objects.get(pk=sorted_cards[i]['id'])
#                 #     temp_locations.append(x)
#                 temp_list = temp_list[:3]
#     except:
#         messages.error(request, 'Please enter the correct specialty along with address!')

#     if not_found:
#         actual_locations = temp_list

#     else:

#         actual_locations = sorted(actual_locations, key=lambda o: o['distance'])
#     specialties = Specialty.objects.all()
#     if request.user.is_authenticated:
#         favorite_locations = sorted(favorite_locations, key=lambda o: o['distance'])
#     context = {
#         'specialties': specialties,
#         'actual_locations': actual_locations,
#         'obj': obj,
#         'check': check,
#         'actual_provider_locations': actual_provider_locations,
#         'favorite_locations': favorite_locations
#     }
#     return render(request, 'accounts/filters.html', context)

def provider(request, office_name):
    data = dict()
    temp_provider = []
    provider_flags = None
    profile = Firm.objects.get(office_name=office_name, account_type='Provider')
    provider = Provider.objects.get(providerprofile=profile)
    reviews = Review.objects.filter(given_to=provider)

    check=False
    xprofile = None
    userprofile = None
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff:
        try:
            xprofile = Firm.objects.get(user=request.user)
            if xprofile.account_type == 'Marketer':
                userprofile = Marketer.objects.get(marketerprofile=xprofile)
            elif xprofile.account_type == 'Attorney':
                userprofile = Attorney.objects.get(attorneyprofile=xprofile)
                for x in userprofile.flag.all():
                    temp_provider.append(x.provider)
                provider_flags = Flagged.objects.filter(provider=provider)

        except:
            try:
                userprofile = MarketerStaff.objects.get(user=request.user, account_type='MarketerStaff')
            except:
                userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
                for x in userprofile.created_by.flag.all():
                    temp_provider.append(x.provider)
                provider_flags = Flagged.objects.filter(provider=provider)
            check=True




    temp_rat = []
    for x in reviews:
        temp_rat.append((x.rating*100)/5)

    if request.method == "POST":
        rating = request.POST.get('rating')
        xcheck = False
        try:
            x_profile = Firm.objects.get(user=request.user, account_type='Attorney')
            attorney = Attorney.objects.get(attorneyprofile=x_profile)
        except:
            attorney = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
            xcheck = True
        description = request.POST.get('description')
        post_as = request.POST.get('anonymous')
        if xcheck:
            review = Review.objects.create(given_by=attorney.created_by, given_to=provider, rating=rating, description=description, post_as=post_as)
            review.save()
        else:
            review = Review.objects.create(given_by=attorney, given_to=provider, rating=rating, description=description, post_as=post_as)
            review.save()
        sum = 0

        print(reviews)
        reviews = Review.objects.filter(given_to=provider)
        for x in reviews:
            sum += float(x.rating)
        count = Review.objects.filter(given_to=provider).count()
        total = 5 * count
        sum = int((sum*100)/total)
        provider.review_percentage = sum
        provider.save()
        messages.success(request, 'Your review has been posted!')
    print(userprofile)
    if check and request.user.is_authenticated:
        userprofile = userprofile.created_by
    context = {
        'data': data,
        'provider': provider,
        'reviews':reviews,
        'temp_rat': temp_rat,
        'userprofile': userprofile,
        'temp_provider': temp_provider,
        'provider_flags': provider_flags,
        'check':check,
    }
    return render(request, 'accounts/provider.html', context)



def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')

def admin_searchbyaddress(request):
    provider = None
    locations = None
    if request.method == "POST":
        try:
            name = request.POST.get('name')
            # temp_locations = Location.objects.all()
            # for location in temp_locations:
            #     temp_address = location.address + ' ' + location.address2 + ' ' + location.city + ' ' + location.state + ' ' + location.country + ' ' + location.post_code
            locations = Location.objects.filter(Q(address__icontains=name) | Q(address2__icontains=name) | Q(city__icontains=name) | Q(state__icontains=name) | Q(country__icontains=name) | Q(post_code__icontains=name))
        except:

            messages.error(request, 'Operations Failed! Please enter the correct Office Name.')
    context = {
        'locations':locations
    }
    return render(request, 'accounts/admin_dashboard.html', context)

def admin_editprovider(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    try:
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            office_name = request.POST.get('office_name')
            email = request.POST.get('email')
            description = request.POST.get('description')
            website = request.POST.get('website')
            fb_page = request.POST.get('fb_page')
            twitter_page = request.POST.get('twitter_page')
            google_page = request.POST.get('google_page')


            provider.providerprofile.first_name = first_name
            provider.providerprofile.last_name = last_name
            provider.providerprofile.office_name = office_name
            provider.providerprofile.email = email
            provider.providerprofile.save()
            provider.description = description
            provider.website = website
            provider.fb_page = fb_page
            provider.twitter_page = twitter_page
            provider.google_page = google_page
            provider.save
            messages.success(request, 'Provider Account has been updated!')
            return redirect('admin_dashboard')
    except:
        messages.error(request, 'Operation Failed! Please try again.')
    context = {
        'provider':provider
    }
    return render(request, 'accounts/admin_editprovider.html', context)

def addProviderIndividual(request):
    if request.method == 'POST':
        try:
            print("hello -----------")
            office_name = request.POST.get('office_name')
            address1 = request.POST.get('address1')
            city1 = request.POST.get('city1')
            state1 = request.POST.get('state1')

            address3 = request.POST.get('address3')
            postal1 = request.POST.get('postal1')
            longitude1 = request.POST.get('longitude1')
            latitude1 = request.POST.get('latitude1')
            phone1 = request.POST.get('phone1')
            fax1 = request.POST.get('fax1')
            email1 = request.POST.get('email1')
            specialties = request.POST.getlist('specialties')
            specialties = [int(i) for i in specialties]
            S=15
            username = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
            password = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
            hashed_pwd = make_password(password)

            user = User.objects.create(username=username, password=hashed_pwd)
            user.save()
            firm = Firm.objects.create(user=user, office_name=office_name, account_type='Provider')
            firm.save()

            provider = Provider.objects.create(providerprofile=firm)
            provider.save()

            location = Location.objects.create(added_by=provider,address=address1,address2=address3, city=city1, state=state1, post_code=postal1,
                            longitude=longitude1, latitude=latitude1, fax=fax1, phone=phone1, email=email1
                            )

            location.save()
            for specialty in specialties:
                obj = Specialty.objects.get(pk=specialty)
                location.specialties.add(obj)
            location.save()

            bill_request_type = 'Medical Bill Request Location'
            record_request_type = 'Medical Record Request Location'
            bill_payment_request_type = 'Medical Bill Request Payment Location'
            record_payment_request_type = 'Medical Record Request Payment Location'
            input_address = str(address1) + ', ' + str(address3) + ', ' + str(city1) + ', ' + str(state1) +  ', '  + str(postal1)
            bill_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                phone=phone1,  email=email1,
                                address_type=bill_request_type
                                )
            bill_request_location.save()

            record_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                    phone=phone1,  email=email1,
                                    address_type=record_request_type
                                    )
            record_request_location.save()

            bill_payment_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                    phone=phone1, email=email1,
                                    address_type=bill_payment_request_type
                                    )
            bill_payment_request_location.save()

            record_payment_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                    phone=phone1, email=email1,
                                    address_type=record_payment_request_type
                                    )
            record_payment_request_location.save()
            messages.success(request, 'Provider has been added successfully!')
        except:
            messages.error(request, 'Operation Failed! Please try uploading the file again!')


    return redirect('admin_importproviders')






import io
def admin_importproviders(request):
    print('noice')
    specialties = Specialty.objects.all()
    if request.method == 'POST':
        csv_file = request.FILES['document']
        print(csv_file.name)
        print(csv_file.size)

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload CSV files to add providers')

        # fs = FileSystemStorage()
        # fs.save(csv_file.name, csv_file)
        # filename = os.path.join(settings.MEDIA_ROOT, csv_file.name)
        data_set = csv_file.read().decode('utf-8-sig')

        io_string = io.StringIO(data_set)

        csvreader = csv.reader(io_string, delimiter=',', quotechar='"')
        S = 15
        provider = None
        try:
            for column in csvreader:

                office_name = column[0]
                specialty = column[1]
                address1 = column[2]
                address2 = column[3]
                city = column[4]
                state = column[5]
                post_code = column[6]
                country = column[7]
                phone= column[8]
                email = column[9]
                website = column[10]
                input_address = str(address1) + ', ' + str(address2) + ', ' + str(city) + ', ' + str(state) + ', ' + str(country) + ', '  + str(post_code)

                api_key = 'AIzaSyBqxc6kyS-LoyaHvVca125NQMefYWI3bn8'
                gmaps_client = googlemaps.Client(api_key)
                geocode_result = gmaps_client.geocode(input_address)
                result = geocode_result[0]

                latitude = result['geometry']['location']['lat']
                longitude = result['geometry']['location']['lng']
                try:
                    # x = Provider.objects.get(providerprofile__office_name=office_name)
                    provider = Provider.objects.get(providerprofile__office_name=office_name)
                except:
                    username = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
                    password = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S))
                    hashed_pwd = make_password(password)

                    user = User.objects.create(username=username, password=hashed_pwd)
                    user.save()
                    firm = Firm.objects.create(user=user, office_name=office_name, account_type='Provider')
                    firm.save()

                    provider = Provider.objects.create(providerprofile=firm, website=website)
                    provider.save()

                location = Location.objects.create(added_by=provider, address=address1, address2=address2,
                            city=city, state=state, post_code=post_code, country=country,
                            longitude=longitude, latitude=latitude, phone=phone, email=email
                )

                location.save()
                bill_request_type = 'Medical Bill Request Location'
                record_request_type = 'Medical Record Request Location'
                bill_payment_request_type = 'Medical Bill Request Payment Location'
                record_payment_request_type = 'Medical Record Request Payment Location'

                bill_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                    phone=phone,  email=email,
                                    address_type=bill_request_type
                                    )
                bill_request_location.save()

                record_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                        phone=phone,  email=email,
                                        address_type=record_request_type
                                        )
                record_request_location.save()

                bill_payment_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                        phone=phone, email=email,
                                        address_type=bill_payment_request_type
                                        )
                bill_payment_request_location.save()

                record_payment_request_location = OtherLocations.objects.create(for_provider=provider, name=input_address,
                                        phone=phone, email=email,
                                        address_type=record_payment_request_type
                                        )
                record_payment_request_location.save()


                temp_specialty = Specialty.objects.get(name=specialty)

                location.specialties.add(temp_specialty)
                location.save()
                messages.success(request, 'Providers and Locations has been added successfully!')
        except:
            messages.error(request, 'Operation Failed! Please try uploading the file again!')

    context = {
        'specialties':specialties
    }
    return render(request, 'accounts/admin_dashboard.html', context)


def createAccount(request):
    return render(request, 'accounts/createAccount.html')


def admin_searchbyoffice(request):
    provider = None

    locations = []
    if request.method == "POST":
        try:
            name = request.POST.get('name')
            print(name)
            providers = Provider.objects.filter(providerprofile__office_name__icontains=name)
            print(providers)
            for provider in providers:
                temp_locations = Location.objects.filter(added_by=provider)
                for location in temp_locations:
                    locations.append({
                        'location':location,
                    })


        except:
            messages.error(request, 'Operations Failed! Please enter the correct Office Name.')
    print(locations)
    context = {
        'locations':locations,

    }
    return render(request, 'accounts/admin_dashboard.html', context)


#case Management

def addBPClient(request):
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)


    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        first_name = first_name.capitalize()
        last_name = last_name.capitalize()
        age = request.POST.get('age')
        address = request.POST.get('address')
        specialty = request.POST.get('specialty')

        gender = request.POST.get('gender', 'Male')
        incident_date = request.POST.get('incident_date')
        incident_date = incident_date[:2] + '/' + incident_date[2:4] + '/' + incident_date[4:]
        case_type = request.POST.get('case_type')
        case_type = BPCaseType.objects.get(pk=int(case_type))
        birthday = request.POST.get('birthday')
        birthday = birthday[:2] + '/' + birthday[2:4] + '/' + birthday[4:]
        case_status = request.POST.get('case_status')
        case_status = TFCaseStatus.objects.get(name__icontains=case_status)
        # age = int(float(age))
        age = 30
        print('the age is :', age)
        client = BPClient.objects.create(first_name=first_name, last_name=last_name, birthday=birthday, age=age, gender=gender)
        client.save()
        case = BPCase.objects.create(for_client=client, incident_date=incident_date, case_type=case_type)
        case.save()

        current_date = str(datetime.today().strftime('%m-%d-%Y'))
        requestUpdate = RequestUpdate.objects.create(for_case=case, changed_by=request.user, status_changed_on=current_date)

        requestUpdate.save()

        location = Location.objects.get(pk=int(address))
        print(location)
        specialty = Specialty.objects.get(name=specialty)
        print(specialty)
        client_provider = BPCaseProviders.objects.create(for_case=case, provider=userprofile, location=location, specialty=specialty, tf_case_status=case_status)
        client_provider.save()

        bp_accounting = BPAccounting.objects.create(for_case=case, for_case_provider=client_provider)
        bp_accounting.save()

        #for creating the object of accounting on TF side --> accounting main page and accounting detail page on TF
        tf_accounting = TFAccounting.objects.create(created_by=location.added_by, for_case_provider=client_provider, for_case=case)
        doc_1 = TFDoc.objects.create(for_provider=location.added_by, for_tf_accounting=tf_accounting, page_name='Accounting', document_no='Paid')
        doc_1.save()
        doc_2 = TFDoc.objects.create(for_provider=location.added_by, for_tf_accounting=tf_accounting, page_name='Accounting', document_no='Cleared')
        doc_2.save()

        doc1 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Bills', provider_documents=client_provider)
        doc1.save()
        doc2 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Records', provider_documents=client_provider)
        doc2.save()
        doc3 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 3', provider_documents=client_provider)
        doc3.save()
        doc4 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Document 4', provider_documents=client_provider)
        doc4.save()
        doc5 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='HIPAA', provider_documents=client_provider)
        doc5.save()
        doc6 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Lien', provider_documents=client_provider)
        doc6.save()
        doc7 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='TF Bills', provider_documents=client_provider)
        doc7.save()
        doc8 = BPDoc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='TF Rec', provider_documents=client_provider)
        doc8.save()
        messages.success(request, 'Client has been created successfully!')

        return redirect('case_management')




def editAccounting(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Provider')
        userprofile = Provider.objects.get(providerprofile=profile)


    except:
        userprofile = ProviderStaff.objects.get(user=request.user, account_type='ProviderStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        tf_accounting_id = request.POST.get('tf_accounting_id')
        original = request.POST.get('original')
        original = float(original.replace(",", ""))
        hi_paid = request.POST.get('hi_paid')
        hi_paid = float(hi_paid.replace(",", ""))
        mp_paid = request.POST.get('mp_paid')
        mp_paid = float(mp_paid.replace(",", ""))
        reduction = request.POST.get('reduction')
        reduction = float(reduction.replace(",", ""))

        hi_reduction = request.POST.get('hi_reduction')
        hi_reduction = float(hi_reduction.replace(",", ""))
        patient_payment_value = request.POST.get('patient_payment_value')
        patient_payment_value = float(patient_payment_value.replace(",", ""))
        check_number = request.POST.get('check_number')
        payment_received_date = request.POST.get('payment_received_date')
        if payment_received_date == '':
            payment_received_date = '_/_/_'
        
        
        tf_accounting = TFAccounting.objects.get(pk=int(tf_accounting_id))
       

        liens = float(original) - (float(hi_paid) + float(hi_reduction) + float(mp_paid) + float(reduction) + float(patient_payment_value))
        final_amount = float(float(hi_paid) + float(mp_paid) + float(patient_payment_value) + float(liens))
        payments = float(float(hi_paid) + float(mp_paid) + float(patient_payment_value))
        reductions = float(float(hi_reduction) + float(reduction))
        tf_accounting.original = float(original)
        tf_accounting.hi_paid = float(hi_paid)
        tf_accounting.mp_paid = float(mp_paid)
        tf_accounting.hi_reduction = float(hi_reduction)
        tf_accounting.reduction = float(reduction)
        tf_accounting.reductions = float(reductions)
        tf_accounting.payments = float(payments)
        tf_accounting.patient_payment_value = float(patient_payment_value)
        liens = '{:.2f}'.format(liens)
        tf_accounting.liens = float(liens)
        tf_accounting.check_number = check_number
        final_amount = '{:.2f}'.format(final_amount)
        tf_accounting.final = float(final_amount)
        tf_accounting.payment_received_date = payment_received_date
        tf_accounting.save()
        
    return redirect('accounting')