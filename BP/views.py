


import csv
import io
import json
from logging import critical
import mimetypes
from pickle import NONE
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from urllib3 import HTTPResponse

from BP.serializers import ReportingAgencySerializer, ClientStatusSerializer, DocSerializer
from accounts.views import firm_users

from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from accounts.models import Specialty, Location, Provider, TFTreatmentDate, TFAccounting, TFDoc
import googlemaps, re
import datetime
import calendar as temp_calendar

from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.db.models import Q

from django.http import HttpResponseRedirect
# Create your views here.

import os
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
from django.views.decorators.clickjacking import xframe_options_sameorigin

from io import StringIO, BytesIO
from docx.shared import Cm
from docxtpl import DocxTemplate, InlineImage

from datetime import datetime as dt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .forms import Doc_Template_Update_Form
from PyPDF2 import PdfFileWriter, PdfFileReader
from fpdf import FPDF

import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from django.utils.crypto import get_random_string
import os, imaplib, email
#-----------
from html.parser import HTMLParser
import re
class HTMLFilter(HTMLParser):
    text = ""
    def handle_data(self, data):
        self.text += data

# http://127.0.0.1:8000/BP/inbox/50/43/
def inbox(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
        
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    documents = Doc.objects.filter(for_client=client, for_case=case)
    case_type_id = []
    case_type_id.append(case.case_type.id)
    page = Page.objects.get(case_types__id__in=case_type_id, name='Inbox')
    
    for doc in documents:
        doc.pages = ocr_Page.objects.filter(document=doc)

    context = {
        'client':client,
        'case': case,
        'documents':documents,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/inbox.html', context)

from BP.management.commands.ocr_cron import apply_OCR
def apply_ocr_manual_trigger(request):
    # jairo
    # http://127.0.0.1:8000/BP/apply_ocr_manual_trigger
    apply_OCR()
    return HttpResponse("apply_ocr_manual_trigger done!")

# def employment(request, client_id, case_id):
#     client = Client.objects.get(pk=client_id)
#     case = Case.objects.get(pk=case_id)
#     context = {
#         'client':client,
#         'case': case
#     }
#     return render(request, 'BP/Employment.html', context)


def get_inbox(host,username, password, client, case):
    mail = imaplib.IMAP4_SSL(host)
    mail.login(username, password)
    mail.select("inbox")
    criteria = f'FROM "{client.email}" UNSEEN'
    print(criteria)
    _, search_data = mail.search(None, criteria)
    my_message = []
    for num in search_data[0].split():
        email_data = {}
        _, data = mail.fetch(num, '(RFC822)')
        # print(data[0])
        _, b = data[0]
        email_message = email.message_from_bytes(b)
        for header in ['subject', 'to', 'from', 'date']:
            # print("{}: {}".format(header, email_message[header]))
            email_data[header] = email_message[header]
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                email_data['html_body'] = body.decode()
            elif part.get_content_type() == "text/html":
                html_body = part.get_payload(decode=True)
                email_data['html_body'] = html_body.decode()
        
        my_message.append(email_data)
        body = email_data['html_body']
        
    # print(my_message)
    for msg in my_message:
        
        body_before_gmail_reply = str(msg['html_body'])
        msg = str(msg['html_body'])
        
        # regex for date format like "On Thu, Mar 24, 2011 at 3:51 PM"
        matching_string_obj = re.search(r"\w+\s+\w+[,]\s+\w+\s+\d+[,]\s+\d+\s+\w+\s+\d+[:]\d+\s+\w+.*", msg)
        if matching_string_obj:
        # split on that match, group() returns full matched string
            body_before_gmail_reply_list = msg.split(matching_string_obj.group())
            # string before the regex match, so the body of the email
            body_before_gmail_reply = body_before_gmail_reply_list[0]
        f = HTMLFilter()
        data = body_before_gmail_reply

        f.feed(data)
        print(f.text)
        temp_body = f.text
        email_obj = Emails.objects.create(for_case=case, for_client=client, created_by=client.client_user, body=temp_body)
        email_obj.save()
    
    return

def sendEmail(smtpHost, smtpPort, mailUname, mailPwd, fromEmail, mailSubject, mailContentHtml, recepientsMailList, attachmentFpaths):
    # create message object
    msg = MIMEMultipart()
    msg['From'] = fromEmail
    msg['To'] = ','.join(recepientsMailList)
    msg['Subject'] = mailSubject
    # msg.attach(MIMEText(mailContentText, 'plain'))
    msg.attach(MIMEText(mailContentHtml, 'html'))

    # create file attachments
    for aPath in attachmentFpaths:
        # check if file exists
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(aPath, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{0}"'.format(os.path.basename(aPath)))
        msg.attach(part)

    # Send message object as email using smptplib
    s = smtplib.SMTP(smtpHost, smtpPort)
    s.starttls()
    s.login(mailUname, mailPwd)
    msgText = msg.as_string()
    sendErrs = s.sendmail(fromEmail, recepientsMailList, msgText)
    s.quit()

    # check if errors occured and handle them accordingly
    if not len(sendErrs.keys()) == 0:
        raise Exception("Errors occurred while sending email", sendErrs)
    return

@login_required
def send_email_firm(request, client_id, case_id):
    check = False
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by

    case = Case.objects.get(pk=int(case_id))
    client = Client.objects.get(pk=client_id)

    # mail server parameters
    smtpHost = "smtp.gmail.com"
    smtpPort = 587
    mailUname = userprofile.attorneyprofile.mailing_email
    mailPwd = userprofile.attorneyprofile.mailing_password
    fromEmail = userprofile.attorneyprofile.office_name + "<" + userprofile.attorneyprofile.mailing_email + ">"

    # mail body, recepients, attachment files
    if request.method == 'POST':
        mail_body = request.POST.get('mail_body')
        greeting = request.POST.get('greeting')
        ending = request.POST.get('ending')
        print('this is mail_body', mail_body)
        mail_body = str(mail_body)
        temp_mail_body = mail_body
        greeting = str(greeting)
        ending = str(ending)
        mailSubject = f"Communication regarding your case ({case.incident_date}) from your law firm ({userprofile.attorneyprofile.office_name})."
        mail_body = greeting + "<br/> <br/>" + mail_body + "<br/> <br/>" + ending
        mailContentHtml = mail_body
        recepientsMailList = [client.email]
        attachmentFpaths = []
        sendEmail(smtpHost, smtpPort, mailUname, mailPwd, fromEmail,
                mailSubject, mailContentHtml, recepientsMailList, attachmentFpaths)

        print("execution complete...")
        email = Emails.objects.create(created_by=request.user, for_client=client, for_case=case, body=temp_mail_body)
        email.save()
        messages.success(request, 'Email has been sent successfully!')

    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


def automated_email_for_credentials(user, client_id, password):
    check = False
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by

    client = Client.objects.get(pk=client_id)

    # mail server parameters
    smtpHost = "smtp.gmail.com"
    smtpPort = 587
    mailUname = userprofile.attorneyprofile.mailing_email
    mailPwd = userprofile.attorneyprofile.mailing_password
    fromEmail = userprofile.attorneyprofile.office_name + "<" + userprofile.attorneyprofile.mailing_email + ">"

    mail_body = f"""
        You can use these credentials to login to the Client Portal <br/> <br/> Username: {client.client_user.username} <br/> Password: {password} <br/> <br/>
    """
    print('this is mail_body', mail_body)
    mail_body = str(mail_body)
    
    mailSubject = "Credentials for Client's Portal"
    mailContentHtml = mail_body
    recepientsMailList = [client.email]
    attachmentFpaths = []
    sendEmail(smtpHost, smtpPort, mailUname, mailPwd, fromEmail,
            mailSubject, mailContentHtml, recepientsMailList, attachmentFpaths)

    print("execution complete...")
    return 



@login_required
def email_credentials(request):
    check = False
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        check = True
    if not check:
        if request.method == 'POST':
            mailing_email = request.POST.get('mailing_email')
            mailing_password = request.POST.get('mailing_password')
            profile.mailing_email = mailing_email
            profile.mailing_password = mailing_password
            profile.save()
            messages.success(request, 'Credentials has been stored Successfully!')
    else:
        messages.error(request, 'Operation Failed! Please try again!')
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
    
@login_required
def clientPortal(request, client_id):
    client = Client.objects.get(pk=client_id)
    cases = Case.objects.filter(for_client=client)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    case_type_id = []
    case_type_id.append(case.case_type.id)
    page = Page.objects.get(case_types__id__in=case_type_id, name='Case')
    context = {
        'cases': cases,
        'client': client,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/client-portal.html', context)

def send_chat_message(request, client_id, case_id):
    check = False
    profile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    thread_user = userprofile.attorneyprofile.user
    client = Client.objects.get(pk=client_id)
    thread = Thread.objects.get(Q(first_person=thread_user, second_person=client.client_user) | Q(first_person=client.client_user, second_person=thread_user))
    print(thread)
    if request.method == 'POST':
        message = request.POST.get('chat_message')
        print(message)
    chat_message = ChatMessage.objects.create(thread=thread, user=thread_user, message=message, sender_name=request.user.username)
    chat_message.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

@login_required
def message_page(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    check = False
    profile = None
    thread_user = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
        thread_user = userprofile.attorneyprofile.user
    except:
        try:
            userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
            userprofile = userprofile.created_by
            thread_user = userprofile.attorneyprofile.user
        except:
            thread_user = client.client_user
    
    threads = Thread.objects.by_user(user=thread_user).prefetch_related('chatmessage_thread')
    pages = Page.objects.all()
    actual_user = thread_user
    current_user = request.user
    context = {
        'Threads': threads,
        'pages':pages,
        'client':client,
        'case':case,
        'actual_user':actual_user,
        'current_user':current_user,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,

    }
    return render(request, 'BP/messages.html', context)


@api_view(['GET'])
def clickLog(request):
    print('this is clickRecord')
    print('Hello')
    # case_id = request.GET.get('case_id')
    # page_id = request.GET.get('page_id')
    # click_id = int(request.GET.get('click_id'))
    
    
    # user = request.user
    # # try:
    # case = Case.objects.get(pk=int(case_id))
    # client = case.for_client
    # page = Page.objects.get(pk=page_id)
    
    # click_log = ClickLog.objects.create(click=click_id, user=request.user, for_case=case, for_client=client, for_firm=client.created_by, for_page=page)
    # click_log.save()

    # # click_record = ClickRecord.objects.create(click=click_id, user=user, for_case=case, for_client=client, for_page=page, for_firm=client.created_by, clickIDName=clickIDDescription)
    # # click_record.save()
    # return JsonResponse({'message': 'ClickLog has been added!'})
    # # except:
    # #       # pragma: no cover
    # #     return JsonResponse({'message': 'We have some error'})

class ListDoc(APIView):
    def get(self, request):

        doc_id = self.request.query_params['doc_id']
        try:
            doc = Doc.objects.get(pk=int(doc_id))
            serializer = DocSerializer(doc, many=False)
            return Response({'data': serializer.data, 'message': 'Doc not found!'})
        except:
            return Response({'message': 'Doc not found!'})
        

        


        return Response({'message': 'done'})

@api_view(['GET'])
def clickRecord(request):
    
    print('Hello')
    try:
        case_id = request.GET.get('case_id')
        page_id = request.GET.get('page_id')
        click_id = request.GET.get('click_id')
        # clickIDDescription = request.GET.get('clickIDDescription')
        
        user = request.user
        # try:
        case = Case.objects.get(pk=int(case_id))
        client = case.for_client
        page = Page.objects.get(pk=page_id)
        
        # click = Click.objects.get(click_id=int(click_id))
        click_record = ClickRecord.objects.create(click=int(click_id), user=request.user, for_case=case, for_client=client, for_firm=client.created_by, for_page=page)
        click_record.save()
        return JsonResponse({'message': 'ClickRecord has been added!'})
    except:
        print('No Click ID with this name!')
        return JsonResponse({'message': 'Something goes Wrong!'})

    # click_record = ClickRecord.objects.create(click=click_id, user=user, for_case=case, for_client=client, for_page=page, for_firm=client.created_by, clickIDName=clickIDDescription)
    # click_record.save()
    
    # except:
    #       # pragma: no cover
    #     return JsonResponse({'message': 'We have some error'})




    


@xframe_options_sameorigin
def open_file(request, doc_id):
    
    doc = Doc.objects.get(pk=doc_id)
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

class MainView(TemplateView):
    template_name = 'BP/main.html'

class GetCaseStatus(APIView):
    def get(self, request):
        case_stage= self.request.query_params['case_stage']
        obj = CaseStage.objects.get(pk=int(case_stage))
        case_status = obj.case_statuses.all()
        serializer = ClientStatusSerializer(case_status, many=True)
        return Response(serializer.data)

class GetReportingAgencyByName(APIView):
    def get(self, request):
        reporting_agency_name = self.request.query_params['name']
        obj = ReportingAgency.objects.get(name__icontains=reporting_agency_name)
        serializer = ReportingAgencySerializer(obj, many=False)
        return Response(serializer.data)

class GetReportingAgencyByCity(APIView):
    def get(self, request):
        city = self.request.query_params['city']
        obj = ReportingAgency.objects.get(city__icontains=city)
        serializer = ReportingAgencySerializer(obj, many=False)
        return Response(serializer.data)

def search_attorneys(request):
    
    bp_attorneys = None
    if request.method == 'POST':
        search = request.POST.get('search')
        print(search)
        bp_attorneys = Attorney.objects.filter(Q(attorneyprofile__office_name__icontains=search))
        print(bp_attorneys) 
    context = {
        
        'bp_attorneys':bp_attorneys
    }
    return render(request, 'BP/search_attorneys.html', context)

def clientProfilePic(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        my_file = request.FILES.get('file')
        client.profile_pic = my_file
        client.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def get_context(client_id, case_id, defendant_id, witness_id, provider_id, other_party_id, incident_report_id):
    

    try:
        client = Client.objects.get(pk=int(client_id))
        client_address = ClientLocation.objects.get(added_by=client)
        case = Case.objects.get(pk=int(case_id))
        firmuser = case.firm_users.all()[0]
        address = client_address.address + ' ' + client_address.address2 + ' ' + client_address.state + client_address.post_code
    except:
        pass
    
    try:
        defendant = Defendant.objects.get(pk=int(defendant_id))
    except:
        pass
    try:
        witness = Witness.objects.get(pk=int(witness_id))
    except:
        pass
    try:
        case_provider = CaseProviders.objects.get(pk=int(provider_id))
    except:
        pass
    try:
        other_party = OtherParty.objects.get(pk=int(other_party_id))
    except:
        pass
    try:
        incident_report = IncidentReport.objects.get(pk=int(incident_report_id))
    except:
        pass

    current_date = datetime.datetime.today().strftime('%m/%d/%Y')
    variables = Variables.objects.all()
    context = {}
    
    for variable in variables:
        try:
            context[variable.name] = eval(variable.value)
        except:
            pass

    print(context)

    print(current_date)
    # return {
    #     'client_first': client.first_name,
    #     'client_last': client.last_name,
    #     'client_address_p1': address,
    #     'client_address_p2': address,
    #     'doi_style1': case.incident_date,
    #     'today_style2': current_date,
    #     'user_ext': firmuser.phone_extension

    # }
    return context

def from_template(template, client_id, case_id, defendant_id, witness_id, provider_id, other_party_id, incident_report_id):
    
    target_file = StringIO()

    template = DocxTemplate(template)
 
    context = get_context(client_id, case_id, defendant_id, witness_id, provider_id, other_party_id, incident_report_id)  # gets the context used to render the document


    # context['signature'] = sign
    print(context)  # adds the InlineImage object to the context
    print('hehehe')
    target_file = BytesIO()
    template.render(context)
    template.save(target_file)
    return target_file

def fillTemplate(request):
    
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        client_id = request.POST.get('client_id')
        case_id = request.POST.get('case_id')
        defendant_id = request.POST.get('defendant_id')
        witness_id = request.POST.get('witness_id')
        provider_id = request.POST.get('provider_id')
        other_party_id = request.POST.get('other_party_id')
        incident_report_id = request.POST.get('incident_report_id')


        if template_id == 'no_option':
            return redirect('bp-client', client.id, case.id)
        letter_template = LetterTemplate.objects.get(pk=int(template_id))
        template = letter_template.template
        file_path = template.url
        print(file_path)
        print('hello')
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = base_dir + file_path
        thefile = file_path
        filename = os.path.basename(thefile)
        print('this is the document url: ', thefile)
        document = from_template(thefile, client_id, case_id, defendant_id, witness_id, provider_id, other_party_id, incident_report_id)
        document.seek(0)
        print(document)
        
        # chunk_size = 20480
        # response = StreamingHttpResponse(FileWrapper(document, chunk_size),
        #     content_type=mimetypes.guess_type(thefile)[0])
        # response['Content-Length'] = os.path.getsize(thefile)
        # response['Content-Disposition'] = "filename=%s" % filename
        response = HttpResponse(content=document)
        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response['Content-Disposition'] = 'attachment; filename="%s.docx"' \
                                        % 'whatever'
        return response


def createWaterMark(filePath,Y, X, Font, Size, Text):
    pdf = FPDF(format='Letter')
    pdf.add_page()
    pdf.set_font(Font, size=Size)
    pdf.set_text_color(0,0,0)
    for count, value in enumerate(Text):
        pdf.text(x=X, y=(Y+6*count), txt=value)
    print('Path for watermark is: ', filePath)
    pdf.output(filePath)


def createPDF(filePathOriginal, filePathWatermark, Y=5, X=5, Font='Arial', Size=10, target_page=2, Text="Default watermark"):
    createWaterMark(filePathWatermark, Y, X, Font, Size, Text)
    
    # output = PdfFileWriter()
    # input = PdfFileReader(open("2022-06-09_SILVERTHORNE.pdf", "rb"))
    # watermark = PdfFileReader(open("temp.pdf", "rb"))

    # for page in range(0,input.getNumPages()):
    #     current_page = input.getPage(page)
    #     if page == target_page - 1:
    #         current_page.mergePage(watermark.getPage(0))

    #     output.addPage(current_page)

    # outputStream = open("new_file1.pdf", "wb")
    # output.write(outputStream)
    # outputStream.close()

def uploadHIPAATemplate(request):
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
          
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by

    if request.method == 'POST':
       
        my_file = request.FILES.get('file')
        x_value = request.POST.get('x_value')
        y_value = request.POST.get('y_value')
        template = None
        try:
            template = HIPAADoc.objects.get(for_firm=userprofile)
        except:
            doc = Doc.objects.create(file_name='HIPAA Doc', page_name='HIPAA', document_no='HIPAA Doc')
            doc.save()
            template = HIPAADoc.objects.create(for_firm=userprofile, template=doc)
            template.save()
        template.x_value = x_value
        template.y_value = y_value
        if template.template.check:
            template.template.upload.delete()
            template.watermark.delete()
            template.template.save()
            template.save()
        template.template.upload = my_file
        template.template.check = True
        template.template.save()
        template.watermark = my_file
        template.save()
        
        

        file_path_watermark = template.watermark.url
        file_path_original = template.template.upload.url
        print('this is the path for watermark: ', file_path_watermark)
        print('this is the path for orginal: ', template.template.upload.url)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_watermark = base_dir + file_path_watermark
        file_path_original = base_dir + file_path_original
        thefile = file_path_watermark
        createPDF(file_path_original, file_path_watermark, Y=50, X=28, Font='Arial', Size=12, target_page=1, Text=["Hospital 1", "123 Anytown land, suite 123", "Phoenix, AZ 92929"])
        
            
    return redirect('bp-firmsetting')

def uploadTemplate(request):
    # client = Client.objects.get(pk=client_id)
    # case = Case.objects.get(pk=case_id)

    if request.method == 'POST':
        try:
            my_file = request.FILES.get('file')
            name = request.POST.get('name')
            category = request.POST.get('category')
            print(my_file)
            letter_template = LetterTemplate.objects.create(template=my_file, template_name=name, template_type=category)
            letter_template.save()
            messages.success(request, 'Template has been added successfully')
        except:
            messages.error(request, 'Operation Failed! Please try Again.')
    


def upload(request, client_id, case_id, doc_id):
    # print(request.FILES)
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    doc = Doc.objects.get(pk=doc_id)
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

def deleteDocument(request, client_id, case_id, document_id):
    try:
        doc = Doc.objects.get(pk=document_id)
        doc.upload.delete()
        doc.check = 'False'
        doc.save()
        print('In delete MEthod')
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
    except:
        JsonResponse({'post':'false'})

def addScheduledToDo(request):
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
          
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    clients = Client.objects.filter(created_by=userprofile)
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        due_date = request.POST.get('due_date')
        note = request.POST.get('note')
        repeat = request.POST.get('repeat')
        statuses = request.POST.getlist('statuses')
        print(statuses)
        
        attorneystaff_user = AttorneyStaff.objects.get(pk=int(user_type))
        current_date = datetime.date.today()
   
        if due_date == '1 day':
            current_date = current_date + datetime.timedelta(days=1)
        elif due_date == '2 days':
            current_date = current_date + datetime.timedelta(days=2)
        elif due_date == '3 days':
            current_date = current_date + datetime.timedelta(days=3)
        elif due_date == '4 days':
            current_date = current_date + datetime.timedelta(days=4)
        elif due_date == '5 days':
            current_date = current_date + datetime.timedelta(days=5)
        elif due_date == '6 days':
            current_date = current_date + datetime.timedelta(days=6)
        elif due_date == '1 week':
            current_date = current_date + datetime.timedelta(days=7)
        elif due_date == '2 weeks':
            current_date = current_date + datetime.timedelta(days=14)
        elif due_date == '1 month':
            current_date = current_date + datetime.timedelta(days=30)
        elif due_date == '2 months':
            current_date = current_date + datetime.timedelta(days=60)
        elif due_date == '6 months':
            current_date = current_date + datetime.timedelta(days=180)
    for client in clients:
        cases = Case.objects.filter(for_client=client)
        for case in cases:
            todo = ToDo.objects.create(created_by=request.user, for_client=client, for_case=case, due_date=current_date, todo_for=attorneystaff_user, notes=note, time='00:00:00', days_to_repeat=repeat)
            todo.last_updated = todo.created_at
            todo.save()
            for x in statuses:
                status = Status.objects.get(pk=int(x))
                todo.case_status.add(status)
                todo.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))  

def addToDo(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    print('hello')
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
          
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        due_date = request.POST.get('due_date')
        note = request.POST.get('note')
        
        attorneystaff_user = AttorneyStaff.objects.get(pk=int(user_type))
        current_date = datetime.date.today()
   
        if due_date == '1 day':
            current_date = current_date + datetime.timedelta(days=1)
        elif due_date == '2 days':
            current_date = current_date + datetime.timedelta(days=2)
        elif due_date == '3 days':
            current_date = current_date + datetime.timedelta(days=3)
        elif due_date == '4 days':
            current_date = current_date + datetime.timedelta(days=4)
        elif due_date == '5 days':
            current_date = current_date + datetime.timedelta(days=5)
        elif due_date == '6 days':
            current_date = current_date + datetime.timedelta(days=6)
        elif due_date == '1 week':
            current_date = current_date + datetime.timedelta(days=7)
        elif due_date == '2 weeks':
            current_date = current_date + datetime.timedelta(days=14)
        elif due_date == '1 month':
            current_date = current_date + datetime.timedelta(days=30)
        elif due_date == '2 months':
            current_date = current_date + datetime.timedelta(days=60)
        elif due_date == '6 months':
            current_date = current_date + datetime.timedelta(days=180)

        todo = ToDo.objects.create(created_by=request.user, for_client=client, for_case=case, due_date=current_date, todo_for=attorneystaff_user, notes=note, time='00:00:00')
        todo.save()
        print(todo)
        page = Page.objects.get(name='To-Do')
        description = 'To-Do for '+ attorneystaff_user.user_type.name + ' due in ' + str(current_date) + ': ' + note 
        note = Notes.objects.create(created_by=request.user, for_client=client, for_case=case, category=page, description=description)
        note.save()
        click = Click.objects.get(click_id=27)
        click_record = ClickRecord.objects.create(click=click, user=request.user, for_case=case, for_client=client, for_firm=client.created_by)
        click_record.save()
        # click_record = ClickRecord.objects.create(click="27", user=request.user, for_case=case, for_client=client, for_page=page, for_firm=client.created_by, clickIDName="New To-Do")
        # click_record.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
            
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def todoCompleted(request, client_id, case_id):
    case = Case.objects.get(pk=int(case_id))
    if request.method == "POST":
        note = request.POST.get('note')
        todo_id = request.POST.get('todo_id')
        todo_id = int(todo_id)
        todo = ToDo.objects.get(pk=todo_id)
        if todo.todo_type == 'Update Requested':
            current_date = str(dt.today().strftime('%m-%d-%Y'))
            request_update = RequestUpdate.objects.get(for_case=case)
            request_update.recent_status = note
            request_update.isRequested = False
            request_update.status_changed_on = current_date
            request_update.request_count = 0
            request_update.save()
        todo.completed_note = note
        todo.status = 'Completed'
        current_date = datetime.date.today()
        todo.completed_at = current_date
        todo.save()
        
        
        print(todo)
        try:
            profile = Firm.objects.get(user=request.user, account_type='Attorney')
            userprofile = Attorney.objects.get(attorneyprofile=profile)
          
        except:
            userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
            userprofile = userprofile.created_by
        page = Page.objects.get(name='To-Do')
        notes = Notes.objects.create(created_by=request.user, for_client=todo.for_client, for_case=todo.for_case, category=page, description=note)
        notes.save()
    return redirect('bp-todo', client_id, case_id)
    

def addCosts(request, client_id, case_id, cost_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    cost_obj = None
    userprofile = None
    try:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
    except:
        pass
    try:
        cost_obj = Costs.objects.get(pk=cost_id)
    except:
        pass

    if request.method == 'POST':
        date = request.POST.get('date')
        payee = request.POST.get('payee')
        invoice_number = request.POST.get('invoice_number')
        amount = request.POST.get('amount')
        paid_by = request.POST.get('paid_by')
        check_number = request.POST.get('check_number')
        check_date = request.POST.get('check_date')
        final_amount = request.POST.get('final_amount')
        memo = request.POST.get('memo')
        check_type = ChequeType.objects.get(name='Costs')
        if not cost_obj:
            doc = Doc.objects.create(for_client=client, for_case=case, document_no='Document')
            doc.save()
            if paid_by == 'Check':
                check = Check.objects.create(cheque_date=check_date, cheque_number=check_number, amount=amount, 
                        payee=payee, cheque_type=check_type, memo=memo, created_by=userprofile, for_case=case
                )
                check.save()
                cost_obj = Costs.objects.create(for_client=client, for_case=case, date=date, invoice_number=invoice_number, paid_by=paid_by,
                            final_amount=final_amount, document=doc, cheque=check
                            )
        
                cost_obj.save()
            else:
                cost_obj = Costs.objects.create(for_client=client, for_case=case, date=date, invoice_number=invoice_number, paid_by=paid_by,
                            final_amount=final_amount, document=doc, amount=amount
                            )
                cost_obj.save()
        else:
          
            if paid_by == 'Credit Card' and cost_obj.cheque:
                print('goes into first')
                print(paid_by)
                cheque = Check.objects.get(pk=cost_obj.cheque.id)
                cheque.delete()
                cost_obj.date = date
                cost_obj.amount = amount
                cost_obj.invoice_number = invoice_number
                cost_obj.paid_by = paid_by
                cost_obj.final_amount = final_amount
                cost_obj.cheque = None
                cost_obj.save()
            elif paid_by == 'Credit Card' and not cost_obj.cheque:
                print('goes into second')
                cost_obj.date = date
                
                cost_obj.invoice_number = invoice_number
                cost_obj.amount = amount
                cost_obj.paid_by = paid_by
                
                
                
                cost_obj.final_amount = final_amount
                
                cost_obj.save()
            elif paid_by == 'Check' and cost_obj.cheque:
                print('goes into third')
                cost_obj.date = date
                cost_obj.cheque.payee = payee
                cost_obj.invoice_number = invoice_number
                cost_obj.cheque.amount = amount
                cost_obj.cheque.memo = memo
                cost_obj.paid_by = paid_by
                cost_obj.cheque.cheque_number = check_number
                cost_obj.cheque.cheque_date = check_date
                cost_obj.cheque.amount = amount
                cost_obj.final_amount = final_amount
                cost_obj.cheque.save()
                cost_obj.save()

        return redirect('bp-costs', client.id, case.id)
    
    context = {
        'client':client,
        'case':case,
        'cost_obj':cost_obj,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }

    return render(request, 'BP/addCosts.html', context)

def flagPage(request, client_id, case_id, flaggedPage, link):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    flagPage = FlaggedPage.objects.create(for_client=client, for_case=case, flagged_by=request.user, page_name=flaggedPage, page_link=link)
    flagPage.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def removeFlagPage(request, client_id, case_id, flaggedpage_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    flagPage = FlaggedPage.objects.get(pk=flaggedpage_id)
    flagPage.delete()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def attachProvider(request, client_id, case_id, location_id, specialty_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    location = Location.objects.get(pk=location_id)
    specialty = Specialty.objects.get(pk=specialty_id)
    client_provider = CaseProviders.objects.create(for_case=case, location=location, provider=location.added_by, specialty=specialty)
    client_provider.save()
    bp_accounting = BPAccounting.objects.create(for_case=case, for_case_provider=client_provider)
    bp_accounting.save()

    #for creating the object of accounting on TF side --> accounting main page and accounting detail page on TF
    tf_accounting = TFAccounting.objects.create(created_by=location.added_by, for_case_provider=client_provider, for_case=case)
    doc_1 = TFDoc.objects.create(for_provider=location.added_by, for_tf_accounting=tf_accounting, page_name='Accounting', document_no='Paid')
    doc_1.save()
    doc_2 = TFDoc.objects.create(for_provider=location.added_by, for_tf_accounting=tf_accounting, page_name='Accounting', document_no='Cleared')
    doc_2.save()

    doc1 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Bill', provider_documents=client_provider)
    doc1.save()
    doc2 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Record', provider_documents=client_provider)
    doc2.save()
    doc3 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Open 1', provider_documents=client_provider)
    doc3.save()
    doc4 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Open 2', provider_documents=client_provider)
    doc4.save()
    doc5 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='HIPAA', provider_documents=client_provider)
    doc5.save()
    doc6 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='Lien', provider_documents=client_provider)
    doc6.save()
    doc7 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='TF Bills', provider_documents=client_provider)
    doc7.save()
    doc8 = Doc.objects.create(for_client=client, for_case=case, page_name='Medical Treatment', document_no='TF Rec', provider_documents=client_provider)
    doc8.save()

    doc = Doc.objects.create(for_client=client, for_case=case, document_no='Document')
    doc.save()
    treatment_date = TreatmentDates.objects.create(for_provider=client_provider, date=case.incident_date, document=doc)
    treatment_date.save()
    return redirect('bp-medicaltreatment', client_id, case_id)

def addProviders(request, client_id, case_id):
    obj = None   
    profile = None
    locations = None
    specialties = Specialty.objects.all()
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    try:
        profile = Firm.objects.get(user=request.user)
        if profile.account_type == 'Attorney':
            userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
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


            print(obj.name)
            
            print('its the specialty')

            locations = Location.objects.filter(specialties=obj)
            locations = locations.filter(Q(address__icontains=address) | Q(city__icontains=city) | Q(state__icontains=state))

            print(locations)
           
    except:
        messages.error(request, 'Please enter the correct specialty along with address!')
    
    
    context = {
        'locations':locations,
        'specialties':specialties,
        'obj':obj,
        'client_id':client_id,
        'case_id': case_id,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addProviders.html', context)

def register(request):
    account_type = 'Attorney'
    user_types = AttorneyUserType.objects.all()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = request.POST.get('email')
            
            first_name = request.POST.get('first_name')
            office_name = request.POST.get('office_name')
            last_name = request.POST.get('last_name')
            user_type = request.POST.get('user_type')
            user_type = AttorneyUserType.objects.get(name='Attorney')
            address1 = request.POST.get('address1')
            city1 = request.POST.get('city1')
            state1 = request.POST.get('state1')
            # country1 = request.POST.get('country1')
            address3 = request.POST.get('address3')
            postal1 = request.POST.get('postal1')
           
            phone1 = request.POST.get('phone1')
            fax1 = request.POST.get('fax1')
            email1 = request.POST.get('email1')
        
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            case_ids = json.dumps([])

            recent_cases = RecentCases.objects.create(user=user, case_ids=case_ids)
            recent_cases.save()
            # account_type = request.POST.get('account_type', 'Provider')
            userprofile = Firm.objects.create(user = user, office_name=office_name, first_name=first_name, last_name=last_name, account_type=account_type)
            userprofile.save()
           
            if account_type == 'Attorney':
                attorney = Attorney.objects.create(attorneyprofile=userprofile,  user_type=user_type)
                attorney.save()
                
            attorney_location = AttorneyLocation.objects.create(added_by=attorney,address=address1,address2=address3, city=city1, state=state1, post_code=postal1,
                        fax=fax1, phone=phone1, email=email1)
            attorney_location.save()
            login(request, user)
            return redirect('bp-home')
    else:
        form = UserCreationForm()
    
    return render(request, 'BP/register.html', {'form':form, 'user_types':user_types}) 

def addTeam(request):
    if request.method == 'POST':
        users = request.POST.getlist('users')
        user_id = request.POST.get('user_id')
        staff = AttorneyStaff.objects.get(pk=int(user_id))

        for user in users:
            x = AttorneyStaff.objects.get(pk=int(user))
            staff.team.add(x)
        staff.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addUsers(request):
    profile = Firm.objects.get(user=request.user)
    user_types = AttorneyUserType.objects.all()
    if profile.account_type == 'Attorney':
        userprofile = Attorney.objects.get(attorneyprofile=profile)

    if request.method == 'POST':
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_extension = request.POST.get('phone_extension')
        temp_user_types = request.POST.getlist('user_types')
        
        

        
        hashed_pwd = make_password(password)
    
        user = User.objects.create(username=username, password=hashed_pwd, first_name=first_name, last_name=last_name, email=email)
        user.save()
        case_ids = json.dumps([])

        recent_cases = RecentCases.objects.create(user=user, case_ids=case_ids)
        recent_cases.save()
        if profile.account_type == 'Attorney':
            staff = AttorneyStaff.objects.create(user=user, created_by=userprofile, phone_extension=phone_extension)
            for temp_user_type in temp_user_types:
                x = AttorneyUserType.objects.get(pk=int(temp_user_type))
                staff.user_type.add(x)
            staff.save()

        return redirect('bp-firmsetting')
        
 
    context = {
        'userprofile': userprofile,
        'user_types':user_types
    }
    return render(request, 'BP/firm-setting.html', context)

def addnotes(request, client_id, case_id):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
          
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    
    if request.method == 'POST':
        description = request.POST.get('description')
        category = request.POST.get('category')
        print(category)
        page = Page.objects.get(pk=int(category))
        note = Notes.objects.create(created_by=request.user, for_client=client, for_case=case, category=page, description=description)
        note.save()
        # click = Click.objects.get(click_id=28)
        
        click_record = ClickRecord.objects.create(click=1, user=request.user, for_case=case, for_client=client, for_firm=client.created_by, for_page=page)
        click_record.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
    
    context = {
        'client':client,
        'case':case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
       
    }

    return render(request, 'BP/addNotes.html', context)

def addNotes(request, client_id, case_id):
    
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
          
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    notes = Notes.objects.filter(for_case=case)
    if request.method == 'POST':
        description = request.POST.get('description')
        category = request.POST.get('category')
        print(category)
        page = Page.objects.get(pk=int(category))
        note = Notes.objects.create(created_by=request.user, for_client=client, for_case=case, category=page, description=description)
        note.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
    
    context = {
        'client':client,
        'case':case,
        'notes':notes,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }

    return render(request, 'BP/note.html', context)

def addClient(request):
    client = None
    check = False
    client_statuses = ClientStatus.objects.all()
    case_stages = CaseStage.objects.all()
    case_types = CaseType.objects.all()
    # try:
    #     profile = Firm.objects.get(user=request.user, account_type='Attorney')
    #     userprofile = Attorney.objects.get(attorneyprofile=profile)
        
        
    # except:
    userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
    # userprofile = userprofile.created_by
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender', 'Male')
        incident_date = request.POST.get('incident_date')
        case_type = request.POST.get('case_type')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        birthday = request.POST.get('birthday')
        address1 = request.POST.get('address1')
        
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        post_code = request.POST.get('post_code')
        age = int(float(age))
        case_status = request.POST.get('case_status')
        case_stage = request.POST.get('case_stage')
        case_status = ClientStatus.objects.get(pk=int(case_status))
        case_stage = CaseStage.objects.get(pk=int(case_stage))
        case_type = CaseType.objects.get(pk=int(case_type))
        print('the age is :', age)
        client = Client.objects.create(created_by=userprofile.created_by, first_name=first_name, last_name=last_name, email=email, phone=phone, birthday=birthday, age=age, gender=gender)
        username = first_name + last_name
        username = username.replace(' ', '')
        username += get_random_string(length=7)
        print('Username is: ', username)
        password = get_random_string(length=16)
        hashed_pwd = make_password(password)
        client_user = User.objects.create(username=username, password=hashed_pwd, first_name=first_name, last_name=last_name, email=email)
        case_ids = json.dumps([])

        recent_cases = RecentCases.objects.create(user=client_user, case_ids=case_ids)
        recent_cases.save()
        client.client_user = client_user
        client.client_user.save()
        client.save()

        try:
            thread = Thread.objects.create(first_person=userprofile.created_by.attorneyprofile.user, second_person=client.client_user)
            thread.save()
        except:
            pass
        # try:
        #     thread = Thread.objects.create(first_person=userprofile.user, second_person=client.client_user)
        #     thread.save()
        # except:
        #     pass
        address = ClientLocation.objects.create(added_by=client, address=address1, address2=address2, city=city, state=state, post_code=post_code)
        address.save()
        case = Case.objects.create(created_by=request.user, for_client=client, incident_date=incident_date, case_type=case_type, case_status=case_status, case_stage=case_stage)
        case.save()
        caseType = case.case_type
        user_types = caseType.user_types.all()
        temp_users = []
        for x in userprofile.team.all():
            temp_users.append(x)
        if len(temp_users) >= 6:
            temp_users = temp_users[:5]
        for temp_user in temp_users:
            case.firm_users.add(temp_user)
            # try:
            #     thread = Thread.objects.create(first_person=temp_user.user, second_person=client.client_user)
            #     thread.save()
            # except:
            #     pass
        
        case.save()
        current_date = str(dt.today().strftime('%m-%d-%Y'))
        

        
        requestUpdate = RequestUpdate.objects.create(for_case=case, changed_by=request.user, status_changed_on=current_date)

        requestUpdate.save()

        automated_email_for_credentials(request.user, client.id, password)
        return redirect('bp-client', client.id, case.id)
    context = {
        'client_statuses':client_statuses,
        'case_types':case_types,
        'case_stages':case_stages
    }
    
    return render(request, 'BP/addClient.html', context)

def dogbite(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)

    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {

        'case':case,
        'client':client,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/dogbite.html', context)

def home(request):
    return render(request, 'BP/home.html')

def addNewCase(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)


    context = {
        'client':client,
        'case':case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addNewCase.html', context)

def addCase(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    check = False
    client_statuses = ClientStatus.objects.all() 
    case_types = CaseType.objects.all()
    case_stages = CaseStage.objects.all()
    # try:
    #     profile = Firm.objects.get(user=request.user, account_type='Attorney')
    #     userprofile = Attorney.objects.get(attorneyprofile=profile)
        
        
    # except:
    userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
    
        
    if request.method == 'POST':
        
        incident_date = request.POST.get('incident_date')
        case_type = request.POST.get('case_type')
        case_type = CaseType.objects.get(pk=int(case_type))
        case_status = request.POST.get('case_status')
        case_stage = request.POST.get('case_stage')
        case_status = ClientStatus.objects.get(pk=int(case_status))
        case_stage = CaseStage.objects.get(pk=int(case_stage))
        new_case = Case.objects.create(created_by=request.user, for_client=client, incident_date=incident_date, case_type=case_type, case_status=case_status, case_stage=case_stage)
        new_case.save()
        temp_users = []
        for x in userprofile.team.all():
            temp_users.append(x)
        if len(temp_users) >= 6:
            temp_users = temp_users[:5]
        for temp_user in temp_users:
            new_case.firm_users.add(temp_user)
            # try:
            #     thread = Thread.objects.create(first_person=temp_user.user, second_person=client.client_user)
            #     thread.save()
            # except:
            #     pass
        
        new_case.save()
        try:
            thread = Thread.objects.create(first_person=userprofile.created_by.attorneyprofile.user, second_person=client.client_user)
            thread.save()
        except:
            pass
        # try:
        #     thread = Thread.objects.create(first_person=userprofile.user, second_person=client.client_user)
        #     thread.save()
        # except:
        #     pass
        current_date = str(dt.today().strftime('%m-%d-%Y'))
        requestUpdate = RequestUpdate.objects.create(for_case=new_case, changed_by=request.user, status_changed_on=current_date)

        requestUpdate.save()
        
        return redirect('bp-client', client.id, case.id)
    context = {
        'client':client,
        'case':case,
        'client_statuses':client_statuses,
        'case_types':case_types,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addCase.html', context)

def changeCaseStage(request, client_id, case_id):
    case = Case.objects.get(pk=case_id)
    client = Client.objects.get(pk=client_id)
    previous_case_stage = case.case_status.name
    if request.method == 'POST':
        case_status = request.POST.get('case_status')
        case_stage = request.POST.get('case_stage')
        case_status = ClientStatus.objects.get(pk=int(case_status))
        case_stage = CaseStage.objects.get(pk=int(case_stage))
        case.case_stage = case_stage
        case.case_status = case_status
        case.save()
        requestUpdate = RequestUpdate.objects.get(for_case=case)
        current_date = str(dt.today().strftime('%m-%d-%Y'))
        requestUpdate.status_changed_on = current_date
        requestUpdate.changed_by = request.user
        temp_note = f'Case status was changed from "{previous_case_stage}" to "{case.case_status.name} Completed" by {request.user.first_name} {request.user.last_name} on {current_date}'
        requestUpdate.recent_status = temp_note
        request.request_count = 0
        requestUpdate.save()
        return redirect('bp-case', client.id, case.id)

def editOtherPartyHomeContact(request):
    if request.method == 'POST':
        party_id = request.POST.get('party_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        party = OtherParty.objects.get(pk=int(party_id))
        party.party_first_name = first_name
        party.party_last_name = last_name
        party.party_home_contact.address1 = address1
        party.party_home_contact.address2 = address2
        party.party_home_contact.city = city
        party.party_home_contact.state = state
        party.party_home_contact.fax = fax
        party.party_home_contact.phone_number = phone
        party.party_home_contact.zip = zip
        party.party_home_contact.email = email
        party.party_home_contact.save()
        party.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editWitnessHomeContact(request):
    if request.method == 'POST':
        witness_id = request.POST.get('witness_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        witness = Witness.objects.get(pk=int(witness_id))
        witness.witness_first_name = first_name
        witness.witness_last_name = last_name
        witness.witness_contact_home.address1 = address1
        witness.witness_contact_home.address2 = address2
        witness.witness_contact_home.city = city
        witness.witness_contact_home.state = state
        witness.witness_contact_home.fax = fax
        witness.witness_contact_home.phone_number = phone
        witness.witness_contact_home.zip = zip
        witness.witness_contact_home.email = email
        witness.witness_contact_home.save()
        witness.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editOtherPartyWorkContact(request):
    if request.method == 'POST':
        party_id = request.POST.get('party_id')
        party_employer = request.POST.get('party_employer')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        party = OtherParty.objects.get(pk=int(party_id))
        party.party_employer = party_employer
        if not party.party_contact_last:
            contact = Contact.objects.create(address1=address1, address2=address2, city=city, state=state, fax=fax, zip=zip, email=email, phone_number=phone)
            contact.save()
            party.party_contact_last = contact
            party.save()
        else:
            party.party_contact_last.address1 = address1
            party.party_contact_last.address2 = address2
            party.party_contact_last.city = city
            party.party_contact_last.state = state
            party.party_contact_last.fax = fax
            party.party_contact_last.phone_number = phone
            party.party_contact_last.zip = zip
            party.party_contact_last.email = email
            party.party_contact_last.save()
            party.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editWitnessWorkContact(request):
    if request.method == 'POST':
        witness_id = request.POST.get('witness_id')
        witness_employer = request.POST.get('witness_employer')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        witness = Witness.objects.get(pk=int(witness_id))
        witness.witness_employer = witness_employer
        if not witness.witness_contact_last:
            contact = Contact.objects.create(address1=address1, address2=address2, city=city, state=state, fax=fax, zip=zip, email=email, phone_number=phone)
            contact.save()
            witness.witness_contact_last = contact
            witness.save()
        else:
            witness.witness_contact_last.address1 = address1
            witness.witness_contact_last.address2 = address2
            witness.witness_contact_last.city = city
            witness.witness_contact_last.state = state
            witness.witness_contact_last.fax = fax
            witness.witness_contact_last.phone_number = phone
            witness.witness_contact_last.zip = zip
            witness.witness_contact_last.email = email
            witness.witness_contact_last.save()
            witness.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editDefendantWorkContact(request):
    if request.method == 'POST':
        defendant_id = request.POST.get('defendant_id')
        defendant_employer = request.POST.get('defendant_employer')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        defendant = Defendant.objects.get(pk=int(defendant_id))
        defendant.defendant_employer = defendant_employer
        if not defendant.work_contact:
            contact = Contact.objects.create(address1=address1, address2=address2, city=city, state=state, fax=fax, zip=zip, email=email, phone_number=phone)
            contact.save()
            defendant.work_contact = contact
            defendant.save()
        else:
            defendant.work_contact.address1 = address1
            defendant.work_contact.address2 = address2
            defendant.work_contact.city = city
            defendant.work_contact.state = state
            defendant.work_contact.fax = fax
            defendant.work_contact.phone_number = phone
            defendant.work_contact.zip = zip
            defendant.work_contact.email = email
            defendant.work_contact.save()
            defendant.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


def editDefendantHomeContact(request):
    if request.method == 'POST':
        defendant_id = request.POST.get('defendant_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        defendant = Defendant.objects.get(pk=int(defendant_id))
        defendant.first_name = first_name
        defendant.last_name = last_name
        defendant.home_contact.address1 = address1
        defendant.home_contact.address2 = address2
        defendant.home_contact.city = city
        defendant.home_contact.state = state
        defendant.home_contact.fax = fax
        defendant.home_contact.phone_number = phone
        defendant.home_contact.zip = zip
        defendant.home_contact.email = email
        defendant.home_contact.save()
        defendant.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addDefendants(request, client_id, case_id):
    case = Case.objects.get(pk=case_id)
    client = Client.objects.get(pk=client_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)


    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        # birthday = request.POST.get('birthday')
        # age = request.POST.get('age')
        # ssn = request.POST.get('ssn')
        # driver_license = request.POST.get('driver_license')
        # defendant_type = request.POST.get('defendant_type','Private Individual')

        # company = request.POST.get('company')
        # policy_no = request.POST.get('policy_no')
        # claim_no = request.POST.get('claim_no')
        # adjuster_name = request.POST.get('adjuster_name')
        # adjuster_address = request.POST.get('adjuster_address')
        # adjuster_phone = request.POST.get('adjuster_phone')
        # adjuster_fax = request.POST.get('adjuster_fax')
        # adjuster_email = request.POST.get('adjuster_email')

        # statute_date = ''
        # car_accident = carAccident.objects.get(for_client=client, for_case=case)
        # date = car_accident.date
        # temp_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        # note = request.POST.get('note')
        # if float(age) > 0:
        #     age = int(float(age))
        # else:
        #     age = 0
        home_contact = Contact.objects.create(address1=address1, address2=address2, city=city, state=state, zip=zip, phone_number=phone, email=email, fax=fax)
        home_contact.save()
        defendant = Defendant.objects.create(first_name = first_name, last_name = last_name, home_contact=home_contact,
                    for_client=client, for_case=case
                    )
        defendant.save()
        # if defendant.defendant_type == 'Private Individual' or defendant.defendant_type == 'Private Company':
        #     if defendant.age < 18:
        #         child_date = datetime.datetime.strptime(birthday, '%Y-%m-%d')
        #         statute_date = add_months(child_date, 240)
        #     else:
        #         statute_date = add_months(temp_date, 24)
        # elif defendant.defendant_type == 'Public Entity':
        #     statute_date = add_months(temp_date, 6)
        # defendant.statute_date = statute_date
        # defendant.save()
        
        # insurance = Insurance.objects.create(for_defendant=defendant, company=company, policy_no=policy_no, claim_no=claim_no,
        #             adjuster_name=adjuster_name, adjuster_address = adjuster_address, adjuster_phone = adjuster_phone, adjuster_fax=adjuster_fax,
        #             adjuster_email=adjuster_email
        #             )
        # insurance.save()
        return redirect('bp-defendants', client.id, case.id)
    context = {
        'client':client,
        'case':case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addDefendants.html', context)

def addOtherParty(request, client_id, case_id):
    case = Case.objects.get(pk=case_id)
    client = Client.objects.get(pk=client_id)

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        contact = Contact.objects.create(address1=address1, address2=address2, email=email, phone_number=phone, city=city, state=state, fax=fax, zip=zip)
        contact.save()
        other_party = OtherParty.objects.create(for_case=case, for_client=client, party_first_name=first_name, party_last_name=last_name, party_home_contact=contact)
        other_party.save()
        # first_name = request.POST.get('first_name')
        # last_name = request.POST.get('last_name')
        # address1 = request.POST.get('address1')
        # address2 = request.POST.get('address2')
        # state = request.POST.get('state')
        # city = request.POST.get('city')
        # zip = request.POST.get('zip')
        # phone = request.POST.get('phone')
        # email = request.POST.get('email')
        # birthday = request.POST.get('birthday')
        # age = request.POST.get('age')
        # ssn = request.POST.get('ssn')
        # driver_license = request.POST.get('driver_license')

        # note = request.POST.get('note')
        # if float(age) > 0:
        #     age = int(float(age))
        # else:
        #     age = 0
        # otherparty = OtherParty.objects.create(first_name = first_name, last_name = last_name, address1=address1,address2=address2, state=state, city=city, post_code=zip, phone=phone, email=email, birthday=birthday,
        #             age=age, ssn=ssn, driver_license=driver_license, note=note, for_client=client, for_case=case
        #             )
        # otherparty.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addWitness(request, client_id, case_id):
    case = Case.objects.get(pk=case_id)
    client = Client.objects.get(pk=client_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)


    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        # birthday = request.POST.get('birthday')
        # age = request.POST.get('age')
        # ssn = request.POST.get('ssn')
        # driver_license = request.POST.get('driver_license')
        # defendant_type = request.POST.get('defendant_type','Private Individual')

        # company = request.POST.get('company')
        # policy_no = request.POST.get('policy_no')
        # claim_no = request.POST.get('claim_no')
        # adjuster_name = request.POST.get('adjuster_name')
        # adjuster_address = request.POST.get('adjuster_address')
        # adjuster_phone = request.POST.get('adjuster_phone')
        # adjuster_fax = request.POST.get('adjuster_fax')
        # adjuster_email = request.POST.get('adjuster_email')

        # statute_date = ''
        # car_accident = carAccident.objects.get(for_client=client, for_case=case)
        # date = car_accident.date
        # temp_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        # note = request.POST.get('note')
        # if float(age) > 0:
        #     age = int(float(age))
        # else:
        #     age = 0
        home_contact = Contact.objects.create(address1=address1, address2=address2, city=city, state=state, zip=zip, phone_number=phone, email=email, fax=fax)
        home_contact.save()
        witness = Witness.objects.create(witness_first_name = first_name, witness_last_name = last_name, witness_contact_home=home_contact,
                    for_client=client, for_case=case
                    )
        witness.save()
        return redirect('bp-witnesses', client.id, case.id)
    context = {
        'client':client,
        'case':case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addWitness.html', context)

def clientLogin(request):
    data = dict()
    
    if request.user.is_authenticated:
        client = None
        try:
            client = Client.objects.get(client_user=request.user)
        except:
            return redirect('bp-searchclient')
        if client:
            return redirect('bp-clientPortal', client.id)
    if request.method == 'POST':
        
        username = request.POST.get('username')
        password = request.POST.get('password1')
        user = authenticate(request, username = username, password = password)
        if user is not None:
            client = Client.objects.get(client_user=user)
            login(request, user)
            return redirect('bp-clientPortal', client.id)
        else:
            print('hello')
            messages.error(request, "Username or password is incorrect")
            return redirect('bp-clientLogin')
    return render(request, 'BP/client-login.html', data)

def loginpage(request):
    data = dict()
    
    if request.user.is_authenticated:
        return redirect('bp-searchclient')
    if request.method == 'POST':
        
        username = request.POST.get('username')
        password = request.POST.get('password1')
        user = authenticate(request, username = username, password = password)
        recent_cases = None
        if user is not None:
            login(request, user)
            try:
                print('I am in this!')
                recent_cases = RecentCases.objects.get(user=request.user) 
                jsonDec = json.decoder.JSONDecoder()
                
                case_ids = jsonDec.decode(recent_cases.case_ids)
                if len(case_ids) == 0:
                    raise Exception("No Recent Case")
                case = Case.objects.get(pk=int(case_ids[-1]))
                return redirect('bp-client', case.for_client.id, case.id)
            except:
                return redirect('bp-searchclient')
        else:
            messages.error(request, "Username or password is incorrect")
    return render(request, 'BP/login-page.html', data)

@login_required(login_url='home')
def logoutPage(request):
    logout(request)
    return redirect('bp-loginpage')

def calculateCaseAge(date_of_incident):
    date_format = "%Y-%m-%d"
    a = dt.strptime(str(dt.now().date()), date_format)
    b = dt.strptime(str(date_of_incident), date_format)
    delta = a - b
    return delta.days

def navigator(request):
    check = False
    user_type = ''
    columns = []
    data = {}
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)   
        check = True
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff') 
        user_type = userprofile.user_type.name
    if not check:
        if request.method == 'POST':
            name = request.POST.get('name1')
            print('heelo')
            print(name)
            if name == 'Case Type':
                
                return redirect('bp-home')
            elif name == 'Medical Providers':
                userprofile1 = AttorneyStaff.objects.filter(user=request.user, account_type='AttorneyStaff') 
                print(userprofile1)
                cases = Case.objects.filter(firm_users__in=userprofile1)
                for case in cases:
                    case_providers = CaseProviders.objects.filter(for_case=case)
                    for case_provider in case_providers:
                        count = 1
                        if case_provider.specialty.name not in data:
                            data[case_provider.specialty.name] = count
                        else:
                            count = data[case_provider.specialty.name]
                            count += 1
                            data[case_provider.specialty.name] = count
                for value in data:
                    columns.append(value)
                context = {
                    'data':data,
                    'columns':columns,
                    'check':check,
                    'user_type':user_type
                }
                return render(request, 'BP/medical-providers.html', context)
            elif name == 'Case Stage':
                userprofile1 = AttorneyStaff.objects.filter(user=request.user, account_type='AttorneyStaff') 
                print(userprofile1)
                cases = Case.objects.filter(firm_users__in=userprofile1)
                for case in cases:
                    print(case)
                    count = 1
                    if case.case_status.name not in data:
                        data[case.case_status.name] = count
                    else:
                        count = data[case.case_status.name]
                        count += 1
                        data[case.case_status.name] = count
                for value in data:
                    columns.append(value)
                context = {
                    'data':data,
                    'columns':columns,
                    'check':check,
                    'user_type':user_type
                }
                return render(request, 'BP/case-stage.html', context)
            elif name == 'Case Injuries':
                userprofile1 = AttorneyStaff.objects.filter(user=request.user, account_type='AttorneyStaff') 
                print(userprofile1)
                cases = Case.objects.filter(firm_users__in=userprofile1)
                for case in cases:
                    injuries = Injury.objects.filter(for_case=case)
                    for injury in injuries:
                        print(case)
                        count = 1
                        if injury.body_part not in data:
                            data[injury.body_part] = count
                        else:
                            count = data[injury.body_part]
                            count += 1
                            data[injury.body_part] = count
                for value in data:
                    columns.append(value)
                context = {
                    'data':data,
                    'columns':columns,
                    'check':check,
                    'user_type':user_type
                }
                return render(request, 'BP/injuries.html', context)
            elif name == 'Case Age':
                temp = [0] * 12
                userprofile1 = AttorneyStaff.objects.filter(user=request.user, account_type='AttorneyStaff') 
                print(userprofile1)
                cases = Case.objects.filter(firm_users__in=userprofile1)
                for case in cases:
                    count = 0
                    if calculateCaseAge(case.incident_date) <= 2:
                        temp[0] += 1
                    elif calculateCaseAge(case.incident_date) <= 5:
                        temp[1] += 1
                    elif calculateCaseAge(case.incident_date) <= 7:
                        temp[2] += 1
                    elif calculateCaseAge(case.incident_date) <= 14:
                        temp[3] += 1
                    elif calculateCaseAge(case.incident_date) <= 21:
                        temp[4] += 1
                    elif calculateCaseAge(case.incident_date) <= 30:
                        temp[5] += 1
                    elif calculateCaseAge(case.incident_date) <= 60:
                        temp[6] += 1
                    elif calculateCaseAge(case.incident_date) <= 90:
                        temp[7] += 1
                    elif calculateCaseAge(case.incident_date) <= 180:
                        temp[8] += 1
                    elif calculateCaseAge(case.incident_date) <= 365:
                        temp[9] += 1
                    elif calculateCaseAge(case.incident_date) <= 730:
                        temp[10] += 1
                    elif calculateCaseAge(case.incident_date) >= 730:
                        temp[11] += 1
                print(temp)
                context = {
                    'check':check,
                    'user_type':user_type,
                    'temp':temp

                }
                return render(request, 'BP/case-age.html', context)

    
    context = {
        'data':data,
        'columns':columns,
        'check':check,
        'user_type':user_type
    }
     
    return render(request, 'BP/index.html', context)

def index(request):
    check = False
    user_type = ''
    columns = []
    data = {}
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)   
        check = True
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff') 
        user_type = userprofile.user_type.name
    if not check:   
        userprofile1 = AttorneyStaff.objects.filter(user=request.user, account_type='AttorneyStaff') 
        print(userprofile1)
        cases = Case.objects.filter(firm_users__in=userprofile1)
        for case in cases:
            print(case)
            count = 1
            if case.case_type not in data:
                data[case.case_type] = count
            else:
                count = data[case.case_type]
                count += 1
                data[case.case_type] = count
        for value in data:
            columns.append(value)
    print(columns)
    print(data)
    print(user_type)
    
    context = {
        'data':data,
        'columns':columns,
        'check':check,
        'user_type':user_type
    }
     
    return render(request, 'BP/index.html', context)

def calendar(request):
    check = False
    event_arr = []
    statute_dates = None
    todo_dates = None
    discovery_dates = None
    litigation_events = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)     
        check = True
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff') 
        userprofile = userprofile.created_by
    if not check:
        temp_id = []
        temp_id.append(userprofile.id)
    cases = Case.objects.filter(for_client__created_by=userprofile)
    firm_users = AttorneyStaff.objects.filter(created_by=userprofile)
    print(cases)
    for case in cases:
        statute_dates = Statute.objects.filter(for_case=case)
        todo_dates = ToDo.objects.filter(for_case=case, status='Not Completed')
        discovery_dates = Discovery.objects.filter(for_case=case)
        litigation_events = LitigationDetails.objects.filter(for_case=case)
    print(litigation_events)
    print('this is discovery events', discovery_dates)
    if litigation_events:
        for litigation in litigation_events:
            event_sub_arr = {}
            event_sub_arr['title'] = litigation.litigation_type + ' ' + litigation.for_client.first_name + ' ' + litigation.for_client.last_name
            event_sub_arr['ID'] = litigation.id
            event_sub_arr['case_id'] = litigation.for_case.id
            event_sub_arr['url'] = 'bp-litigation'
            start_date = datetime.datetime.strptime(str(litigation.date), "%Y-%m-%d").strftime("%Y-%m-%d")
            end_date = datetime.datetime.strptime(str(litigation.end_date), "%Y-%m-%d").strftime("%Y-%m-%d")
            if litigation.time == '00:00:00' and litigation.end_time == '00:00:00':
                event_sub_arr['allDay'] = 'True'
            event_sub_arr['start_date'] = start_date
            event_sub_arr['end_date'] = end_date
            event_sub_arr['start_time'] = litigation.time
            event_sub_arr['end_time'] = litigation.end_time
            event_arr.append(event_sub_arr)
    if statute_dates:
        for statue_date in statute_dates:
            event_sub_arr = {}
            event_sub_arr['title'] = 'Statute' + ' ' + statue_date.for_client.first_name + ' ' + statue_date.for_client.last_name
            event_sub_arr['ID'] = statue_date.id
            event_sub_arr['case_id'] = statue_date.for_case.id
            # if statue_date.time == '00:00:00':
            event_sub_arr['allDay'] = 'True'
            event_sub_arr['url'] = 'bp-statute'
            start_date = datetime.datetime.strptime(str(statue_date.statute_date.date()), "%Y-%m-%d").strftime("%Y-%m-%d")
            event_sub_arr['start_date'] = start_date
            event_sub_arr['end_date'] = start_date
            event_sub_arr['start_time'] = '00:00:00'
            event_sub_arr['end_time'] = '00:00:00'
          
            event_arr.append(event_sub_arr)
    if todo_dates:
        for todo_date in todo_dates:
            event_sub_arr = {}
            event_sub_arr['title'] = 'To-Do' + ' ' + todo_date.for_client.first_name + ' ' + todo_date.for_client.last_name
            event_sub_arr['ID'] = todo_date.id
            event_sub_arr['case_id'] = todo_date.for_case.id
            event_sub_arr['url'] = 'bp-todo'
            start_date = datetime.datetime.strptime(str(todo_date.due_date), "%Y-%m-%d").strftime("%Y-%m-%d")
            event_sub_arr['start_date'] = start_date
            event_sub_arr['end_date'] = start_date
            event_sub_arr['start_time'] = todo_date.time
            if todo_date.time == '00:00:00':
                event_sub_arr['allDay'] = 'True'
            event_sub_arr['end_time'] = '00:00:00'
            
            event_arr.append(event_sub_arr)
    if discovery_dates:
        for discovery_date in discovery_dates:
            event_sub_arr = {}
            event_sub_arr['title'] = 'Discovery'
            event_sub_arr['ID'] = discovery_date.id
            event_sub_arr['case_id'] = discovery_date.for_case.id
            event_sub_arr['url'] = 'bp-discovery'
            start_date = datetime.datetime.strptime(str(discovery_date.due_date), "%Y-%m-%d").strftime("%Y-%m-%d")
            event_sub_arr['start_date'] = start_date
            event_sub_arr['allDay'] = True
            event_arr.append(event_sub_arr)

    print(event_arr)
    context = {
        'events':event_arr,
        'check':check,
        'cases':cases,
        'firm_users':firm_users
    }


    return render(request, 'BP/calendar.html', context)

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, temp_calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)

def rejectClaim(request, client_id, case_id, defendant_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    defendant = Defendant.objects.get(pk=defendant_id)
    if request.method == 'POST':
        date = request.POST.get('date')
        temp_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        statute_date = add_months(temp_date, 6)
        defendant.statute_date = statute_date
        defendant.expiry_date = date
        defendant.claim_rejected = 'True'
        defendant.save()
        return redirect('bp-defendants', client.id, case.id)
    context = {
        'client':client, 
        'case':case,
        'defendant':defendant,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/rejectClaim.html', context)


def addClaim(request, client_id, case_id, defendant_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    defendant = Defendant.objects.get(pk=defendant_id)
    if request.method == 'POST':
        date = request.POST.get('date')
        temp_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        expiry_date = temp_date + datetime.timedelta(days=45)
        expiry_date = expiry_date.strftime('%Y-%m-%d')
        statute_date = temp_date + datetime.timedelta(days=45)
        statute_date = add_months(statute_date, 6)
        # temp_date = statute_date + datetime.timedelta(days=45)
        # statute_date = temp_date.strftime('%Y-%m-%d')
        defendant.statute_date = statute_date
        defendant.claim_date = date
        defendant.expiry_date = expiry_date
        defendant.save()
        return redirect('bp-defendants', client.id, case.id)
    context = {
        'client':client, 
        'case':case,
        'defendant':defendant,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addClaim.html', context)

def addCarAccidentAddress(request, client_id, case_id, car_accident_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    car_accident = None
    try:
        car_accident = carAccident.objects.get(pk=car_accident_id)
    except:
        pass
    if request.method == 'POST':
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        date = request.POST.get('date')
        time = request.POST.get('time')
        weather = request.POST.get('weather')
        description = request.POST.get('description')
        statute_date = ''

        api_key = 'AIzaSyBqxc6kyS-LoyaHvVca125NQMefYWI3bn8'
        gmaps_client = googlemaps.Client(api_key)
        temp_address = address+' '+city+' '+state
        geocode_result = gmaps_client.geocode(temp_address)
        result = geocode_result[0]

        input_latitude = result['geometry']['location']['lat']
        input_longitude = result['geometry']['location']['lng']

        case_defendants = Defendant.objects.filter(for_client=client, for_case=case)
        temp_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        if case_defendants.count() == 0:   
            statute_date = add_months(temp_date, 6)
        else:
            for defendant in case_defendants:
                if defendant.defendant_type == 'Private Individual' or defendant.defendant_type == 'Private Company':
                    statute_date = add_months(temp_date, 24)
                elif defendant.defendant_type == 'Public Entity':
                    statute_date = add_months(temp_date, 6)
                defendant.statute_date = statute_date
                defendant.save()

        print(date)
        print(temp_date)
        # temp_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        
        # temp_date = temp_date + datetime.timedelta(days=365)
        # print(temp_date.strftime('%Y-%m-%d'))
        if car_accident == None:
            car_accident = carAccident.objects.create(for_client=client, for_case=case, address=address,city=city, state=state, date=date,
                            time=time, weather=weather, description=description, lat=input_latitude, long=input_longitude
                            )
            car_accident.save()
        else:
            car_accident.address = address
            car_accident.city = city
            car_accident.state = state
            car_accident.date = date
            car_accident.time = time
            car_accident.weather = weather
            car_accident.description = description
            car_accident.lat = input_latitude
            car_accident.long = input_longitude
            car_accident.save()
        return redirect('bp-caraccident', client.id, case.id)
    context = {
        'client': client,
        'case':case,
        'car_accident': car_accident,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addCarAccidentAddress.html', context)

def caraccident(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    address = ClientLocation.objects.get(added_by=client)
    car_accident = None
    try:
        car_accident = carAccident.objects.get(for_client=client, for_case=case)
    except:
        pass
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Car Accident')
        
    except:
        pass
    page = Page.objects.get(name='Car Accident')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'car_accident':car_accident,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/car-accident.html', context)

def caseage(request):
    return render(request, 'BP/case-age.html')

def caseloan(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    address = ClientLocation.objects.get(added_by=client)
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Case Loan')
        
    except:
        pass
    page = Page.objects.get(name='Case Loans')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/case-loan.html', context)

def casestage(request):
    return render(request, 'BP/case-stage.html')

def casetype(request):
    return render(request, 'BP/case-type.html')

def casevalue(request):
    return render(request, 'BP/case-value.html')

def addCaseUsers(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    user_types = AttorneyUserType.objects.all()
    if request.method == 'POST':
        # case_managers_attach = request.POST.get('case_managers_attach')
        # paralegal_attach = request.POST.get('paralegal_attach')
        # intake_attach = request.POST.get('intake_attach')
        for user_type in user_types:
            x = request.POST.get(user_type.name)
            if x != 'no_option':
                temp = AttorneyStaff.objects.get(pk=int(x))
                case.firm_users.add(temp)
                case.save()
        # if case_managers_attach != 'no_option':
        #     case_manager = AttorneyStaff.objects.get(pk=int(case_managers_attach))
        #     case.firm_users.add(case_manager)
        # if paralegal_attach != 'no_option':
        #     paralegal = AttorneyStaff.objects.get(pk=int(paralegal_attach))
        #     case.firm_users.add(paralegal)
        # if intake_attach != 'no_option':
        #     intake = AttorneyStaff.objects.get(pk=int(intake_attach))
        #     case.firm_users.add(intake)
        
        
        

        
    return redirect('bp-case', client.id, case.id)
    



def case(request, client_id, case_id):

    


    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)


    #to fetch the last 9 cases accessed by current logged in user
    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)
    factors = case.case_type.factors.all()
    # factor_ids = [x.id for x in factors]
    # factor_scales = FactorScale.objects.filter(firm=userprofile, factors__in=factor_ids)
    # factors = FirmRank.objects.filter(firm=userprofile, factor__in=factor_ids)
    print('these are the factors: ', factors)
    total_medical_bill = 0
    total_injury_ratings = 0
    total_policy_limits = 0
    total_liability_percentage = 0
    bp_accountings = BPAccounting.objects.filter(for_case=case)
    case_injuries = Injury.objects.filter(for_case=case)
    case_insurances = Insurance.objects.filter(for_case=case)
    defendants_on_case = Defendant.objects.filter(for_case=case)
    for case_insurance in case_insurances:
        total_policy_limits += max(case_insurance.UMLimit1, case_insurance.liabilityLimit)
    for defendant in defendants_on_case:
        total_liability_percentage += defendant.liability_percent
    for case_injury in case_injuries:
        injury_rating = Injuries.objects.get(pk=case_injury.injury.id)
        total_injury_ratings += int(injury_rating.value)
    
    for bp_accounting in bp_accountings:
        total_medical_bill += int(bp_accounting.original)
    print('Total Medical Bills: ', total_medical_bill)
    print('Total Injury Ratings: ', total_injury_ratings)
    print('Total Policy Limits: ', total_policy_limits)
    print('Total Defendant Liability: ', total_liability_percentage)

    final_case_rank = 0
    total_count = 0
    for factor in factors:
        if factor.name == 'Medical Bills':
            factor_scales = FactorScale.objects.filter(firm=userprofile, factor=factor)
            for factor_scale in factor_scales:
              
                if factor_scale.min <= int(total_medical_bill) and factor_scale.max >= int(total_medical_bill):
                    firm_rank = FirmRank.objects.get(firm=userprofile, factor_scale=factor_scale, case_type=case.case_type)
                    rank_value = Rank.objects.get(pk=firm_rank.rank.id).value
                   
                    final_case_rank += rank_value
                    total_count += 1
                    break
        elif factor.name == 'Injury':
            factor_scales = FactorScale.objects.filter(firm=userprofile, factor=factor)
            for factor_scale in factor_scales:
              
                if factor_scale.min <= int(total_injury_ratings) and factor_scale.max >= int(total_injury_ratings):
                    firm_rank = FirmRank.objects.get(firm=userprofile, factor_scale=factor_scale, case_type=case.case_type)
                    rank_value = Rank.objects.get(pk=firm_rank.rank.id).value
                    print('I am in Injury')
                    final_case_rank += rank_value
                    total_count += 1
                    break
        elif factor.name == 'Policy Limits':
            factor_scales = FactorScale.objects.filter(firm=userprofile, factor=factor)
            for factor_scale in factor_scales:
              
                if factor_scale.min <= int(total_policy_limits) and factor_scale.max >= int(total_policy_limits):
                    firm_rank = FirmRank.objects.get(firm=userprofile, factor_scale=factor_scale, case_type=case.case_type)
                    rank_value = Rank.objects.get(pk=firm_rank.rank.id).value
                   
                    final_case_rank += rank_value
                    total_count += 1
                    break
        elif factor.name == 'Liability Percentage':
            factor_scales = FactorScale.objects.filter(firm=userprofile, factor=factor)
            for factor_scale in factor_scales:
              
                if factor_scale.min <= int(total_liability_percentage) and factor_scale.max >= int(total_liability_percentage):
                    firm_rank = FirmRank.objects.get(firm=userprofile, factor_scale=factor_scale, case_type=case.case_type)
                    rank_value = Rank.objects.get(pk=firm_rank.rank.id).value
                   
                    final_case_rank += rank_value
                    total_count += 1
                    break
    print('this is the final rank value: ', final_case_rank)
    all_ranks = [x.value for x in Rank.objects.all()]
    print('All Ranks: ', all_ranks)
    actual_case_rank = int(final_case_rank/total_count)
    actual_case_rank = all_ranks[min(range(len(all_ranks)), key=lambda i: abs(all_ranks[i]-actual_case_rank))]
    print('Actual Case Rank: ', actual_case_rank)
    case_rank = Rank.objects.get(value=actual_case_rank)
    case.case_rank=case_rank
    case.save()



    
    address = ClientLocation.objects.get(added_by=client)
    case_statuses = ClientStatus.objects.all()
    case_stages = CaseStage.objects.all()
    case_defendants = Defendant.objects.filter(for_client=client, for_case=case)
    temp_dates = []
    
    case_statute_date = ''
    case_type_id = []
    case_type_id.append(case.case_type.id)
    page = Page.objects.get(case_types__id__in=case_type_id, name='Case')
    print('Page is : ', page)
    user_types = AttorneyUserType.objects.all()
    pages = Page.objects.all()
    case_users = case.firm_users.all()
    
    
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    caseType = case.case_type
    case_user_types = caseType.user_types.all()
    temp_users = []
    x = []
    index = 1
    for case_user in case_users:
        temp_users.append(case_user)
    
    index = 0
    counter = 0
    intake_user = AttorneyStaff.objects.get(user=case.created_by)
    for case_user_type in case_user_types:
        if case_user_type.name == 'Intake':
            print('hahah')
            x.append({
                        'user_type':case_user_type,
                        'user':intake_user,
                        'index': index + 1
                    })
                
            index += 1 
        else:
            counter += 1
            if counter <= len(temp_users):
                x.append({
                        'user_type':case_user_type,
                        'user':temp_users[index],
                        'index': index + 1
                    })
                
                index += 1
            else:
                x.append({
                        'user_type':case_user_type,
                        'user':None,
                        'index': index + 1
                    })
                index += 1
    case.firm_users.add(intake_user)
    case.save()

        
        
    # print('this is x:', x)

    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)     
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff') 
        userprofile = userprofile.created_by
    
    # case_managers = AttorneyStaff.objects.filter(created_by=userprofile, user_type='case manager')
    # paralegal = AttorneyStaff.objects.filter(created_by=userprofile, user_type='paralegal')
    # intake = AttorneyStaff.objects.filter(created_by=userprofile, user_type='intake')
    firm_users = AttorneyStaff.objects.filter(created_by=userprofile)
    
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Case')
        print(flagPage)
    except:
        pass

    try:
        for defendant in case_defendants:
            temp_dates.append(defendant.statute_date)
        dates = [datetime.datetime.strptime(ts, "%Y-%m-%d") for ts in temp_dates]
        dates.sort()
        sorteddates = [datetime.datetime.strftime(ts, "%Y-%m-%d") for ts in dates]
        case_statute_date = sorteddates[0]
    except:
        pass
    
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    critical_note = ''
    update_case_status=''
    
    try:
        critical_note_obj = Notes.objects.filter(category__name = 'New Critical Note',for_case= case)
        critical_note = critical_note_obj[0]
        print('Critical Note', critical_note.description)
    except Exception as note_e:
        print(note_e)
   
    try:
        update_case_status_obj = Notes.objects.filter(category__name = 'Update Case Status', for_case=case)
        update_case_status = update_case_status_obj[0]
        print('Update Case status', update_case_status.description)
    except Exception as note_e:
        print(note_e)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'case_statute_date':case_statute_date,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'case_user_types':case_user_types,
        # 'case_managers':case_managers,
        # 'paralegal':paralegal,
        # 'intake':intake,
        'case_users':case_users,
        'firm_users':firm_users,
        'flagPage':flagPage,

        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'user_types':user_types, 
        'temp_x': x,
        'page':page,
        'last_accessed_cases':last_accessed_cases,
        'current_case':current_case,
        'critical_note': critical_note,
        'update_case_status': update_case_status
       
    }
    template_name = str('BP/' + page.html_template_name)
    return render(request, template_name, context)

def checklist(request):
    return render(request, 'BP/checklist.html')

def un_mark_checklist_handler(checklist_id, client_id, case_id):
    print('I ma here in uncheck')
    checklist = CheckList.objects.get(pk=checklist_id)
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    try:
        case_checklists = CaseChecklist.objects.get(checklist=checklist, for_case=case, for_client=client)
        print(case_checklists)
        case_checklists.delete()
    except:
        pass
    
    return

def uncheckChecklist(request, checklist_id, client_id, case_id):
    un_mark_checklist_handler(checklist_id, client_id, case_id)
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def mark_checklist_handler(checklist_id, client_id, case_id):
    checklist = CheckList.objects.get(pk=checklist_id)
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    case_checklists = None
    print('hello I m in new checklist')
    try:
        case_checklists = CaseChecklist.objects.get(checklist=checklist, for_case=case, for_client=client)
    except:
        pass
    if not case_checklists:
        case_checklists = CaseChecklist.objects.create(checklist=checklist, for_case=case, for_client=client, status=True)
    else:
        case_checklists.status = True
    case_checklists.save()
    return

def markChecklist(request, checklist_id, client_id, case_id):
    mark_checklist_handler(checklist_id, client_id, case_id)
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def uncheckPanelChecklist(request,  checklist_id):
    checklist = PanelCaseChecklist.objects.get(pk=checklist_id)
    checklist.delete()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def markPanelChecklist(request, checklist_id, source_id, client_id, case_id, page_name):
    checklist = PanelCheckList.objects.get(pk=checklist_id)
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if page_name == "Medical Treatment":
        case_provider = CaseProviders.objects.get(pk=source_id)
        case_checklists = PanelCaseChecklist.objects.create(checklist=checklist, for_case=case, for_client=client, for_provider=case_provider, status=True)
    elif page_name == 'Defendants':
        defendant = Defendant.objects.get(pk=source_id)
        case_checklists = PanelCaseChecklist.objects.create(checklist=checklist, for_case=case, for_client=client, for_defendant=defendant, status=True)
    elif page_name == 'Witness':
        defendant = Witness.objects.get(pk=source_id)
        case_checklists = PanelCaseChecklist.objects.create(checklist=checklist, for_case=case, for_client=client, for_witness=defendant, status=True)
    elif page_name == 'Other Party':
        defendant = OtherParty.objects.get(pk=source_id)
        case_checklists = PanelCaseChecklist.objects.create(checklist=checklist, for_case=case, for_client=client, for_otherparty=defendant, status=True)
    case_checklists.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))



def client(request, pk, case_id):

    
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    thread_user = userprofile.attorneyprofile.user
    client = Client.objects.get(pk=pk)
    case = Case.objects.get(pk=case_id)
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    address = ''
    try:
        address = ClientLocation.objects.get(added_by=client)
    except:
        pass
    
    templates = LetterTemplate.objects.filter(template_type='Client')
    pages = Page.objects.all()
    case_type_id = []
    case_type_id.append(case.case_type.id)
    page = Page.objects.get(case_types__id__in=case_type_id, name='Client')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Client')
        
    except:
        pass
    
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    
    emails = Emails.objects.filter(for_client=client)
    smtpHost = 'imap.gmail.com'
    smtpPort = 587
    mailUname = userprofile.attorneyprofile.mailing_email
    mailPwd = userprofile.attorneyprofile.mailing_password
    fromEmail = userprofile.attorneyprofile.office_name + "<" + userprofile.attorneyprofile.mailing_email + ">"
    if client.email != '' and not None:
        get_inbox(smtpHost, mailUname, mailPwd, client, case)

    thread = Thread.objects.get(Q(first_person=thread_user, second_person=client.client_user) | Q(first_person=client.client_user, second_person=thread_user))
    current_status_check = [x.id for x in case.auto_case_status.all()]
    current_stage_check = [x.id for x in case.auto_case_stage.all()]
    acts = Act.objects.all()
    check = False
    if userprofile.shakespeare_status:
        for act in acts:
            check = False
            work_units = act.work_units.all().filter(Q(table='Client') | Q(table='Case'))
            for work_unit in work_units:
                choice = ''
                if work_unit.table == 'Client':
                    command = "client."
                elif work_unit.table == 'Case':
                    command = "case."
                if work_unit.valued:
                    print('this is valued')
                    command += work_unit.field
                    temp = eval(command)
                    print('this is actua value', temp)
                    firm_threshold = FirmThresholdValue.objects.get(for_firm=userprofile)
                    firm_value = "firm_threshold."+work_unit.field
                    firm_value = eval(firm_value)
                    print('this is threshold value', firm_value)
                    if work_unit.min and work_unit.min != '' and work_unit.max and work_unit.max != '':
                        print('helelellel')
                        firm_value_min = "firm_threshold."+work_unit.field + '_min'
                        firm_value_max = "firm_threshold."+work_unit.field + '_max'
                        firm_value_min = eval(firm_value_min)
                        firm_value_max = eval(firm_value_max)

                        print('this is firm_value_min', firm_value_min)
                        print('this is firm_value_max', firm_value_max)
                        print('this is temp', temp)
                        if not (int(temp) < int(firm_value_max) and int(temp) > int(firm_value_min)):
                            check = True
                    elif work_unit.less and work_unit.less != '':
                        if not (int(temp) < int(firm_value)):
                            check = True
                    elif work_unit.more and work_unit.more != '':
                        print('this is more')
                        if not (int(temp) > int(firm_value)):
                            check = True
                    if not check:
                        blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                        for current_x in current_status_check:
                            if current_x in blocked_case_status:
                                case_status = Status.objects.get(pk=int(current_x))
                                case.auto_case_status.remove(case_status)
                                case.save()
                                print('hello')
                        if work_unit.checklist:
                            mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    else:
                        if work_unit.checklist:
                            un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)

                elif work_unit.any:
                    print('this is any')
                    command += work_unit.related_name + ".all()"
                    records = eval(command)
                    temp = False
                    for record in records:
                        value = "record." + work_unit.field
                        value = eval(value)
                        if value and value != '' and value != "_/_/_":
                            temp = True
                            break
                    if not temp:
                        check = True
                        if work_unit.checklist:
                            un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    else:
                        blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                        for current_x in current_status_check:
                            if current_x in blocked_case_status:
                                case_status = Status.objects.get(pk=int(current_x))
                                case.auto_case_status.remove(case_status)
                                case.save()
                                print('hello')
                        if work_unit.checklist:
                            mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    print("this is records", records)
                
                elif work_unit.all:
                    print('this is all')
                    command += work_unit.related_name + ".all()"
                    records = eval(command)
                    temp = False
                    for record in records:
                        value = "record." + work_unit.field
                        value = eval(value)
                        if not value or value == '' or value == "_/_/_":
                            temp = True
                            break
                    if temp:
                        check = True
                        if work_unit.checklist:
                            un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    else:
                        blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                        for current_x in current_status_check:
                            if current_x in blocked_case_status:
                                case_status = Status.objects.get(pk=int(current_x))
                                case.auto_case_status.remove(case_status)
                                case.save()
                                print('hello')
                        if work_unit.checklist:
                            mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    print("this is records", records)
                elif work_unit.empty:
                    print('this is empty')
                    command += work_unit.field
                    temp = eval(command)
                    
                    if temp or temp != '':
                        check = True
                        if work_unit.checklist:
                            un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    else:
                        blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                        for current_x in current_status_check:
                            if current_x in blocked_case_status:
                                case_status = Status.objects.get(pk=int(current_x))
                                case.auto_case_status.remove(case_status)
                                case.save()
                                print('hello')
                        if work_unit.checklist:
                            mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                elif work_unit.filled:
                    print('this is filled')
                    command += work_unit.field
                    temp = eval(command)
                    
                    if not temp or temp == '':
                        check = True
                        if work_unit.checklist:
                            un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    else:
                        blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                        for current_x in current_status_check:
                            if current_x in blocked_case_status:
                                case_status = Status.objects.get(pk=int(current_x))
                                case.auto_case_status.remove(case_status)
                                case.save()
                                print('hello')
                        if work_unit.checklist:
                            mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                                
                
                else:
                    command += work_unit.field
                    temp = eval(command)
                    if work_unit.less and work_unit.less != '':
                        print('this is less')
                        if not (int(temp) < int(work_unit.less)):
                            check = True
                    elif work_unit.more and work_unit.more != '':
                        print('this is more')
                        if not (int(temp) > int(work_unit.more)):
                            check = True
                    elif work_unit.min and work_unit.min != '' and work_unit.max and work_unit.max != '':
                        print('this is inb/w')
                        if not (int(temp) < int(work_unit.max) and int(temp) > int(work_unit.min)):
                            check = True
                    
                    if not check:
                        blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                        for current_x in current_status_check:
                            if current_x in blocked_case_status:
                                case_status = Status.objects.get(pk=int(current_x))
                                case.auto_case_status.remove(case_status)
                                case.save()
                                print('hello')
                        if work_unit.checklist:
                            mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    else:
                        if work_unit.checklist:
                            un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
            
            act_case_status = ActCaseStatus.objects.get(act=act)
            try:
                act_case_stage = ActCaseStage.objects.get(act=act)
                case_stage = act_case_stage.stage
            except:
                case_stage = None
            case_status = act_case_status.status
            
            if not check: 
                print('Check is False')   
                if case_status.id not in current_status_check:
                    case.auto_case_status.add(case_status)
                    case.save()
                if case_stage and case_stage.id not in current_stage_check:
                    case.auto_case_stage.add(case_stage)
                    case.save()
            else:
                print('Check is True')
                if case_status.id in current_status_check:
                    case.auto_case_status.remove(case_status)
                    case.save()
                if case_stage and case_stage.id in current_stage_check:
                    case.auto_case_stage.remove(case_stage)
                    case.save()

    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
        
    
    checklist_percentage = 0
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        pass
    client_contact_info = []
    client_obj_1 = client.contact_1
    if client_obj_1 != None:
        client_contact_info.append(client_obj_1)
    client_obj_2 = client.contact_2
    if client_obj_2 != None:
        client_contact_info.append(client_obj_2)
    client_obj_3 = client.contact_3
    if client_obj_3 != None:
        client_contact_info.append(client_obj_3)
    print('Client Contact Info List',client_contact_info )
    context = {
        'userprofile':userprofile,
        'client':client,
        'case':case,
        'client_address':address,
        'templates':templates,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'flagPage':flagPage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'emails':emails,
        'thread':thread,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
        'client_contact_info': client_contact_info,
    }
    template_name = str('BP/' + page.html_template_name)
    return render(request, template_name, context)

def editClientInfo1(request, client_id, case_id):
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        client_phone = request.POST.get('client_phone')
        client_email = request.POST.get('client_email')
        # if client_phone and client_phone != '':
        client.phone = client_phone
        # if client_email and client_email != '':
        client.email = client_email
        client.save()
        current_status_check = [x.id for x in case.auto_case_status.all()]
        current_stage_check = [x.id for x in case.auto_case_stage.all()]
        acts = Act.objects.all()
        check = False
        if userprofile.shakespeare_status:
            for act in acts:
                check = False
                work_units = act.work_units.all().filter(Q(table='Client') | Q(table='Case'))
                for work_unit in work_units:
                    choice = ''
                    if work_unit.table == 'Client':
                        command = "client."
                    elif work_unit.table == 'Case':
                        command = "case."
                    if work_unit.valued:
                        print('this is valued')
                        command += work_unit.field
                        temp = eval(command)
                        print('this is actua value', temp)
                        firm_threshold = FirmThresholdValue.objects.get(for_firm=userprofile)
                        firm_value = "firm_threshold."+work_unit.field
                        firm_value = eval(firm_value)
                        print('this is threshold value', firm_value)
                        if work_unit.min and work_unit.min != '' and work_unit.max and work_unit.max != '':
                            print('helelellel')
                            firm_value_min = "firm_threshold."+work_unit.field + '_min'
                            firm_value_max = "firm_threshold."+work_unit.field + '_max'
                            firm_value_min = eval(firm_value_min)
                            firm_value_max = eval(firm_value_max)

                            print('this is firm_value_min', firm_value_min)
                            print('this is firm_value_max', firm_value_max)
                            print('this is temp', temp)
                            if not (int(temp) < int(firm_value_max) and int(temp) > int(firm_value_min)):
                                check = True
                        elif work_unit.less and work_unit.less != '':
                            if not (int(temp) < int(firm_value)):
                                check = True
                        elif work_unit.more and work_unit.more != '':
                            print('this is more')
                            if not (int(temp) > int(firm_value)):
                                check = True
                        if not check:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)

                    elif work_unit.any:
                        print('this is any')
                        command += work_unit.related_name + ".all()"
                        records = eval(command)
                        temp = False
                        for record in records:
                            value = "record." + work_unit.field
                            value = eval(value)
                            if value and value != '' and value != "_/_/_":
                                temp = True
                                break
                        if not temp:
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        print("this is records", records)
                    
                    elif work_unit.all:
                        print('this is all')
                        command += work_unit.related_name + ".all()"
                        records = eval(command)
                        temp = False
                        for record in records:
                            value = "record." + work_unit.field
                            value = eval(value)
                            if not value or value == '' or value == "_/_/_":
                                temp = True
                                break
                        if temp:
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        print("this is records", records)
                    elif work_unit.empty:
                        print('this is empty')
                        command += work_unit.field
                        temp = eval(command)
                        
                        if temp or temp != '':
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    elif work_unit.filled:
                        print('this is filled')
                        command += work_unit.field
                        temp = eval(command)
                        
                        if not temp or temp == '':
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                                    
                    
                    else:
                        command += work_unit.field
                        temp = eval(command)
                        if work_unit.less and work_unit.less != '':
                            print('this is less')
                            if not (int(temp) < int(work_unit.less)):
                                check = True
                        elif work_unit.more and work_unit.more != '':
                            print('this is more')
                            if not (int(temp) > int(work_unit.more)):
                                check = True
                        elif work_unit.min and work_unit.min != '' and work_unit.max and work_unit.max != '':
                            print('this is inb/w')
                            if not (int(temp) < int(work_unit.max) and int(temp) > int(work_unit.min)):
                                check = True
                        
                        if not check:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                
                act_case_status = ActCaseStatus.objects.get(act=act)
                try:
                    act_case_stage = ActCaseStage.objects.get(act=act)
                    case_stage = act_case_stage.stage
                except:
                    case_stage = None
                case_status = act_case_status.status
                
                if not check: 
                    print('Check is False')   
                    if case_status.id not in current_status_check:
                        case.auto_case_status.add(case_status)
                        case.save()
                    if case_stage and case_stage.id not in current_stage_check:
                        case.auto_case_stage.add(case_stage)
                        case.save()
                else:
                    print('Check is True')
                    if case_status.id in current_status_check:
                        case.auto_case_status.remove(case_status)
                        case.save()
                    if case_stage and case_stage.id in current_stage_check:
                        case.auto_case_stage.remove(case_stage)
                        case.save()

        
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


def editClientInfo2(request, client_id, case_id):
    print('********** edit client info 2 ************')
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    case_provider = CaseProviders.objects.get(for_case = case , for_case__for_client = client)
    primary_phone= ''
    client_phone_list = []
    client_email_list = []
    if request.method == 'POST':
        try:
            client_phone_1 = request.POST.get('client_phone_1')
            client_phone_list.append(client_phone_1)
            client_phone_2 = request.POST.get('client_phone_2')
            client_phone_list.append(client_phone_2)
            client_phone_3 = request.POST.get('client_phone_3')
            client_phone_list.append(client_phone_3)
            contact_obj_1 = client.contact_1
            contact_obj_2 = client.contact_2
            contact_obj_3 = client.contact_3
            print('**** CLient Object', client.first_name, client.last_name)
            if client_phone_1 != None and client_phone_1 != '' :
                
                if contact_obj_1 != None :
                    contact_obj_1.phone_number=client_phone_1
                    contact_obj_1.save()
                else:
                    contact_obj_1=Contact.objects.create( phone_number = client_phone_1)
                    client.contact_1=contact_obj_1
                    client.save()
            if client_phone_2 != None and client_phone_2 != '':
                if contact_obj_2 != None:
                    contact_obj_2.phone_number=client_phone_2
                    contact_obj_2.save()
                else:
                    contact_obj_2=Contact.objects.create( phone_number = client_phone_2)
                    client.contact_2=contact_obj_2
                    client.save()
            if client_phone_3 != None and client_phone_3 != '':   
                if contact_obj_3 != None:
                    contact_obj_3.phone_number=client_phone_3
                    contact_obj_3.save()
                else:   
                    contact_obj_3=Contact.objects.create( phone_number = client_phone_3)
                    client.contact_3=contact_obj_3
                    client.save()

            primary_phone = request.POST.get('primary_phone')
            
            if primary_phone != None and primary_phone != '' :
                prim_contact_obj = Contact.objects.get(phone_number=primary_phone)
                client.primary_phone=prim_contact_obj
                client.save()
        except Exception as p_e:
            print(p_e)


        try:
            client_email_1 = request.POST.get('client_email1')
            
            client_email_2 = request.POST.get('client_email2')
            
            client_email_3 = request.POST.get('client_email3')
            print('Client Email',client_email_1 )
            if client_email_1 == '':
                print('Client Email empty')
            
            contact_obj_1 = client.contact_1
            contact_obj_2 = client.contact_2
            contact_obj_3 = client.contact_3
            
            if client_email_1 != None and client_email_1 != '':
                print('Client Email 1 empty')
                if contact_obj_1 != None :
                    contact_obj_1.email=client_email_1
                    contact_obj_1.save()
                else:
                    contact_obj_1=Contact.objects.create( email = client_email_1)
                    client.contact_1=contact_obj_1
                    client.save()
            if client_email_2 != None and client_email_2 != '':
                print('Client Email 2 empty')
                if contact_obj_2 != None:
                    contact_obj_2.email=client_email_2
                    contact_obj_2.save()
                else:
                    contact_obj_2=Contact.objects.create( email = client_email_2)
                    client.contact_2=contact_obj_2
                    client.save()
            if client_email_3 != None and client_email_3 != '':  
                print('Client Email 3 empty') 
                if contact_obj_3 != None:
                    contact_obj_3.email=client_email_3
                    contact_obj_3.save()
                else:   
                    contact_obj_3=Contact.objects.create( email = client_email_3)
                    client.contact_3=contact_obj_3
                    client.save()
            
            primary_email = request.POST.get('primary_email')
            
            if primary_email != None and primary_email != '' :
                prim_contact_obj = Contact.objects.get(email=primary_email)
                client.primary_email=prim_contact_obj
                client.save()
        except Exception as e_e:
            print(e_e)


        try:
            home_modal_one_address1 = request.POST.get('home_modal_one_address1')
            home_modal_one_address2 = request.POST.get('home_modal_one_address2')
            home_modal_one_city = request.POST.get('home_modal_one_city')
            home_modal_one_state = request.POST.get('home_modal_one_state')
            home_modal_one_zip = request.POST.get('home_modal_one_zip')
            is_email= request.POST.get('is_email')
            
            print('is_email',is_email)
            if home_modal_one_address1 != None :
                print('---------home_modal_one_address1---------')
                contact_obj_1 = client.contact_1
                if contact_obj_1 != None :
                    if home_modal_one_address1 != '':
                        contact_obj_1.address1 = home_modal_one_address1
                    if home_modal_one_address2 != '':
                        contact_obj_1.address2 = home_modal_one_address2
                    if home_modal_one_city != '':
                        contact_obj_1.city = home_modal_one_city
                    if home_modal_one_state != '':
                        contact_obj_1.state = home_modal_one_state
                    if home_modal_one_zip != '':
                        contact_obj_1.zip = home_modal_one_zip
                    contact_obj_1.save()
                    if is_email:
                        client.mailing_contact= contact_obj_1
                else:
                    contact_obj_1 = Contact.objects.create(address1=home_modal_one_address1,address2= home_modal_one_address2, city = home_modal_one_city, state= home_modal_one_state, zip = home_modal_one_zip)
                    client.contact_1=contact_obj_1
                    if is_email:
                        client.mailing_contact= contact_obj_1
                    client.save()

        except Exception as h1_e:
            print(h1_e)
        
        try:

            home_modal_two_address1 = request.POST.get('home_modal_two_address1')
            home_modal_two_address2 = request.POST.get('home_modal_two_address2')
            home_modal_two_city = request.POST.get('home_modal_two_city')
            home_modal_two_state = request.POST.get('home_modal_two_state')
            home_modal_two_zip = request.POST.get('home_modal_two_zip')
            is_email= request.POST.get('is_email')
            


            print('is_email',is_email)
            
            if home_modal_two_address1 != None:  
                print('---------home_modal_two_address1---------')        
                contact_obj_2 = client.contact_2
                if contact_obj_2 != None :
                    
                    if home_modal_two_address1 != '':
                        contact_obj_2.address1 = home_modal_two_address1
                    if home_modal_two_address2 != '':
                        contact_obj_2.address2 = home_modal_two_address2
                    if home_modal_two_city != '':
                        contact_obj_2.city = home_modal_two_city
                    if home_modal_two_state != '':
                        contact_obj_2.state = home_modal_two_state
                    if home_modal_two_zip != '':
                        contact_obj_2.zip = home_modal_two_zip
                    contact_obj_2.save()
                    if is_email:
                        client.mailing_contact= contact_obj_2

                else:
                    contact_obj_2 = Contact.objects.create(for_client = client,address1=home_modal_two_address1,address2= home_modal_two_address2, city = home_modal_two_city, state= home_modal_two_state, zip = home_modal_two_zip)
                    client.contact_2=contact_obj_2
                    if is_email:
                        client.mailing_contact= contact_obj_2
                    client.save()
        except Exception as h2_e:
            print(h2_e)
        
        try:
            emergency_name = request.POST.get('emergency_name')
            emergency_relationship = request.POST.get('emergency_relationship')
            emergency_discuss_case = request.POST.get('discuss_case')
            emergency_phone = request.POST.get('emergency_phone')
            emergency_email = request.POST.get('emergency_email')
            emergency_address1 = request.POST.get('emergency_address1')
            emergency_address2 = request.POST.get('emergency_address2')
            emergency_city = request.POST.get('emergency_city')
            emergency_state = request.POST.get('emergency_state')
            emergency_zip = request.POST.get('emergency_zip')
           
            if emergency_name != None:
                contact_obj_2 = client.emergency_contact
                if contact_obj_2 != None :
                    if emergency_name != '':
                        contact_obj_2.first_name=emergency_name
                    if emergency_relationship != '':
                        contact_obj_2.relationship=emergency_relationship
                    if emergency_discuss_case:
                        contact_obj_2.discussCase=emergency_discuss_case
                    else:
                        contact_obj_2.discussCase= 'False'
                    if emergency_phone != '':
                        contact_obj_2.contact.phone_number=emergency_phone
                    if emergency_address1 != '':
                        contact_obj_2.contact.address1=emergency_address1
                    if emergency_address2 != '':
                        contact_obj_2.contact.address2=emergency_address2
                    if emergency_email != '':
                        contact_obj_2.contact.email=emergency_email
                    if emergency_city != '':
                        contact_obj_2.contact.city=emergency_city
                    if emergency_state != '':
                        contact_obj_2.contact.state=emergency_state
                    if emergency_zip != '':
                        contact_obj_2.contact.zip=emergency_zip
                    
                    contact_obj_2.save()
                    contact_obj_2.contact.save()
                else:
                    if emergency_discuss_case:
                        emergency_discuss_case=emergency_discuss_case
                    else:
                        emergency_discuss_case= 'False'
                    contact_obj = Contact.objects.create(address1=emergency_address1, address2=emergency_address2,city=emergency_city, state=emergency_state, zip=emergency_zip, phone_number=emergency_phone , email=emergency_email)
                    emergency_contact_obj = EmergencyContact.objects.create(first_name=emergency_name,relationship=emergency_relationship,discussCase=emergency_discuss_case, contact =contact_obj )
                    client.emergency_contact = emergency_contact_obj
                    client.save()
            
        except Exception as em_e:

            print(em_e)
        

        
        try:
            medical_address_block_name = request.POST.get('address_block_name')
            medical_address1 = request.POST.get('medical_address1')
            medical_address2 = request.POST.get('medical_address2')
            medical_city = request.POST.get('medical_city')
            medical_state = request.POST.get('medical_state')
            medical_zip = request.POST.get('medical_zip')
            medical_phone = request.POST.get('medical_phone')
            medical_fax = request.POST.get('medical_fax')
            medical_email = request.POST.get('medical_email')
            
            
            print('address_block_name',medical_address_block_name)
            if medical_address_block_name != None :
                if medical_address_block_name == 'treatment_location':
                    contact_obj_1 = case_provider.treatment_location
                if medical_address_block_name == 'records_request':
                    contact_obj_1 = case_provider.records_request
                if medical_address_block_name == 'billing_request':
                    contact_obj_1 = case_provider.billing_request
                if medical_address_block_name == 'billing_request_paid':
                    contact_obj_1 = case_provider.billing_request_paid
                if medical_address_block_name == 'records_request_paid':
                    contact_obj_1 = case_provider.records_request_paid
                if medical_address_block_name == 'lien_holder':
                    contact_obj_1 = case_provider.lien_holder
                if contact_obj_1 != None :
                    if medical_address1 != '':
                        contact_obj_1.address1 = medical_address1
                    if medical_address2 != '':
                        contact_obj_1.address2 = medical_address2
                    if medical_city != '':
                        contact_obj_1.city = medical_city
                    if medical_state != '':
                        contact_obj_1.state = medical_state
                    if medical_zip != '':
                        contact_obj_1.zip = medical_zip
                    if medical_phone != '':
                        contact_obj_1.phone_number = medical_phone
                    if medical_fax != '':
                        contact_obj_1.fax = medical_fax
                    if medical_email != '':
                        contact_obj_1.email = medical_email
                    contact_obj_1.save()
                    
                else:
                    contact_obj_1 = Contact.objects.create(address1=medical_address1,address2= medical_address2, city = medical_city, state= medical_state, zip = medical_zip,phone_number = medical_phone,email = medical_email, fax = medical_fax)
                    if medical_address_block_name == 'treatment_location':
                        case_provider.treatment_location=contact_obj_1
                    if medical_address_block_name == 'records_request':
                        case_provider.records_request=contact_obj_1
                    if medical_address_block_name == 'billing_request':
                        case_provider.billing_request=contact_obj_1
                    if medical_address_block_name == 'billing_request_paid':
                        case_provider.billing_request_paid=contact_obj_1
                    if medical_address_block_name == 'records_request_paid':
                        case_provider.records_request_paid=contact_obj_1
                    if medical_address_block_name == 'lien_holder':
                        case_provider.lien_holder=contact_obj_1
                    
                    case_provider.save()
                   
        except Exception as h1_e:
            print(h1_e)
         
        
        
        client_dob = request.POST.get('client_dob')
        client_ssn = request.POST.get('client_ssn')
        client_driver_license = request.POST.get('client_driver_license')
        print('this is client_dob', client_dob)
        
        print('this is client_ssn', client_ssn)
        if client_dob and client_dob != '':
            client.birthday = client_dob
        if client_ssn and client_ssn != 0:
            client.ssn = int(client_ssn)
        if client_driver_license and client_driver_license != 0:
            client.driver_license_number = client_driver_license
        client.save()
        current_status_check = [x.id for x in case.auto_case_status.all()]
        current_stage_check = [x.id for x in case.auto_case_stage.all()]
        acts = Act.objects.all()
        check = False
        if userprofile.shakespeare_status:
            for act in acts:
                check = False
                work_units = act.work_units.all().filter(Q(table='Client') | Q(table='Case'))
                for work_unit in work_units:
                    choice = ''
                    if work_unit.table == 'Client':
                        command = "client."
                    elif work_unit.table == 'Case':
                        command = "case."
                    if work_unit.valued:
                        print('this is valued')
                        command += work_unit.field
                        temp = eval(command)
                        print('this is actua value', temp)
                        firm_threshold = FirmThresholdValue.objects.get(for_firm=userprofile)
                        firm_value = "firm_threshold."+work_unit.field
                        firm_value = eval(firm_value)
                        print('this is threshold value', firm_value)
                        if work_unit.min and work_unit.min != '' and work_unit.max and work_unit.max != '':
                            print('helelellel')
                            firm_value_min = "firm_threshold."+work_unit.field + '_min'
                            firm_value_max = "firm_threshold."+work_unit.field + '_max'
                            firm_value_min = eval(firm_value_min)
                            firm_value_max = eval(firm_value_max)

                            print('this is firm_value_min', firm_value_min)
                            print('this is firm_value_max', firm_value_max)
                            print('this is temp', temp)
                            if not (int(temp) < int(firm_value_max) and int(temp) > int(firm_value_min)):
                                check = True
                        elif work_unit.less and work_unit.less != '':
                            if not (int(temp) < int(firm_value)):
                                check = True
                        elif work_unit.more and work_unit.more != '':
                            print('this is more')
                            if not (int(temp) > int(firm_value)):
                                check = True
                        if not check:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)

                    elif work_unit.any:
                        print('this is any')
                        command += work_unit.related_name + ".all()"
                        records = eval(command)
                        temp = False
                        for record in records:
                            value = "record." + work_unit.field
                            value = eval(value)
                            if value and value != '' and value != "_/_/_":
                                temp = True
                                break
                        if not temp:
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        print("this is records", records)
                    
                    elif work_unit.all:
                        print('this is all')
                        command += work_unit.related_name + ".all()"
                        records = eval(command)
                        temp = False
                        for record in records:
                            value = "record." + work_unit.field
                            value = eval(value)
                            if not value or value == '' or value == "_/_/_":
                                temp = True
                                break
                        if temp:
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        print("this is records", records)
                    elif work_unit.empty:
                        print('this is empty')
                        command += work_unit.field
                        temp = eval(command)
                        
                        if temp or temp != '':
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                    elif work_unit.filled:
                        print('this is filled')
                        command += work_unit.field
                        temp = eval(command)
                        
                        if not temp or temp == '':
                            check = True
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                                    
                    
                    else:
                        command += work_unit.field
                        temp = eval(command)
                        if work_unit.less and work_unit.less != '':
                            print('this is less')
                            if not (int(temp) < int(work_unit.less)):
                                check = True
                        elif work_unit.more and work_unit.more != '':
                            print('this is more')
                            if not (int(temp) > int(work_unit.more)):
                                check = True
                        elif work_unit.min and work_unit.min != '' and work_unit.max and work_unit.max != '':
                            print('this is inb/w')
                            if not (int(temp) < int(work_unit.max) and int(temp) > int(work_unit.min)):
                                check = True
                        
                        if not check:
                            blocked_case_status = [x.id for x in work_unit.blocked_status.all()]
                            for current_x in current_status_check:
                                if current_x in blocked_case_status:
                                    case_status = Status.objects.get(pk=int(current_x))
                                    case.auto_case_status.remove(case_status)
                                    case.save()
                                    print('hello')
                            if work_unit.checklist:
                                mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                        else:
                            if work_unit.checklist:
                                un_mark_checklist_handler(work_unit.checklist.id, client.id, case.id)
                
                act_case_status = ActCaseStatus.objects.get(act=act)
                try:
                    act_case_stage = ActCaseStage.objects.get(act=act)
                    case_stage = act_case_stage.stage
                except:
                    case_stage = None
                case_status = act_case_status.status
                
                if not check: 
                    print('Check is False')   
                    if case_status.id not in current_status_check:
                        case.auto_case_status.add(case_status)
                        case.save()
                    if case_stage and case_stage.id not in current_stage_check:
                        case.auto_case_stage.add(case_stage)
                        case.save()
                else:
                    print('Check is True')
                    if case_status.id in current_status_check:
                        case.auto_case_status.remove(case_status)
                        case.save()
                    if case_stage and case_stage.id in current_stage_check:
                        case.auto_case_stage.remove(case_stage)
                        case.save()
        
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editShakespeareStatus(request):
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')

    if request.method == 'POST':
        shakespeare_status = request.POST.get('shakespeare_status')
        if shakespeare_status == 'On':
            userprofile.shakespeare_status = True
        else:
            userprofile.shakespeare_status = False
        userprofile.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addThresholdValue(request):
    profile = None
    userprofile = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')

    firm_threshold = FirmThresholdValue.objects.get(for_firm=userprofile)
    if request.method == 'POST':
        property_damage_value = int(request.POST.get('property_damage_value'))
        property_damage_value_min = int(request.POST.get('property_damage_value_min'))
        property_damage_value_max = int(request.POST.get('property_damage_value_max'))
        firm_threshold.property_damage_value = property_damage_value
        firm_threshold.property_damage_value_min = property_damage_value_min
        firm_threshold.property_damage_value_max = property_damage_value_max
        firm_threshold.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
    
def costs(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    costs = Costs.objects.filter(for_client=client,for_case=case)
    paid_costs = Costs.objects.filter(~Q(cheque__cheque_number=''),for_client=client,for_case=case)
    open_costs = Costs.objects.filter(cheque__cheque_number='',for_client=client,for_case=case)
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Cost')
        
    except:
        pass
    total_amount = 0
    for cost in costs:
        total_amount += cost.final_amount
    
    unpaid_amount = 0
    for cost in open_costs:
        unpaid_amount += cost.final_amount

    paid_amount = 0
    for cost in paid_costs:
        paid_amount += cost.final_amount
    page = Page.objects.get(name='Costs')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'costs':costs,
        'paid_costs':paid_costs,
        'open_costs':open_costs,
        'total_amount':total_amount,
        'unpaid_amount':unpaid_amount,
        'paid_amount':paid_amount,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Costs.html', context)

def defendants(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    defendants = Defendant.objects.filter(for_client=client, for_case=case)
    insurance_types = InsuranceType.objects.all()
    templates = LetterTemplate.objects.filter(template_type='Defendants')
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Defendant')
        
    except:
        pass
    page = Page.objects.get(name='Defendants')
    final_checklist = []
    overall_checklist = []
    overall_checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_panelchecklists = 0
    checklist_panelpercentage = {}
    total_marked = 0
    total_panelmarked = {}
    for checklist in overall_checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                overall_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            overall_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
        
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    checklists = PanelCheckList.objects.filter(panel_name=page)
    total_panelchecklists = PanelCheckList.objects.filter(panel_name=page).count()
    for client_provider in defendants:
        panel_case_checklists = PanelCaseChecklist.objects.filter(for_case=case, for_client=client, for_defendant=client_provider)
        count = 0
        for checklist in checklists:
            check = False
            
            for panel_case_checklist in panel_case_checklists:
                if checklist.id == panel_case_checklist.checklist.id:
                    check = True
                    final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':panel_case_checklist.id,
                        'name': checklist.name,
                        
                        'status': True
                    })
                    count += 1
                    
            if not check:
                final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':-1,
                        'name': checklist.name,
                        'status': False,
                    })
            total_panelmarked[client_provider.id] = count
        try:
            checklist_panelpercentage[client_provider.id] = int((total_panelmarked[client_provider.id] * 100)/total_panelchecklists)
        except:
            checklist_panelpercentage[client_provider.id] = 0
    
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    print(final_checklist)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'defendants': defendants,
        'templates': templates,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,

        'overall_checklist':overall_checklist, 
        'checklist_panelpercentage':checklist_panelpercentage,
        'total_panelmarked':total_panelmarked,
        'total_panelchecklists':total_panelchecklists, 
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'insurance_types':insurance_types,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Defendants.html', context)

def depositions(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)

    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    defendants = Defendant.objects.filter(for_client=client, for_case=case)
    depositions = Deposition.objects.filter(for_client=client, for_case=case)
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Deposition')
        
    except:
        pass
    page = Page.objects.get(name='Depositions')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'defendants':defendants,
        'depositions':depositions,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Depositions.html', context)

def addDeposition(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        time = request.POST.get('time')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        taking = request.POST.get('taking')
        location = request.POST.get('location')
        note = request.POST.get('note')
        defending = request.POST.get('defending')
        defendant = Defendant.objects.get(pk=int(defending))
        deposition = Deposition.objects.create(for_client=client, for_case=case, name=name, date=date, time=time, address1=address1,
                    address2=address2, city=city, state=state, zip_code=zip, taking=taking, location=location, note=note,
                    defending=defendant
                    )
        deposition.save()
    return redirect('bp-depositions', client.id, case.id)


def addDiscovery(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    if request.method == 'POST':
        date_served = request.POST.get('date_served')
        due_date = request.POST.get('due_date')
        type = request.POST.get('type')
        description = request.POST.get('date_served')
        from_defendant = request.POST.get('from_defendant')
        to_defendant = request.POST.get('to_defendant')

        from_defendant = Defendant.objects.get(pk=int(from_defendant))
        to_defendant = Defendant.objects.get(pk=int(to_defendant))
        discovery = Discovery.objects.create(for_client=client, for_case=case, date_served=date_served, due_date=due_date,
                                            type=type, description=description, from_defendant=from_defendant, to_defendant=to_defendant
                                            )
        discovery.save()
        return redirect('bp-discovery', client.id, case.id)
    context = {
        'client':client,
        'case': case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Discovery.html', context)


def discovery(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    defendants = Defendant.objects.all()
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Discovery')
        
    except:
        pass
    page = Page.objects.get(name='Discovery')
    litigation_discovery = LitigationDetails.objects.filter(for_client=client,  for_case=case, litigation_type='Discovery')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'defendants':defendants,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'litigation_discovery':litigation_discovery,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Discovery.html', context)

def documents(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Document')
        
    except:
        pass
    page = Page.objects.get(name='Documents')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Documents.html', context)

def employment(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Employment')
        
    except:
        pass
    page = Page.objects.get(name='Employment')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Employment.html', context)

def firmsetting(request):
    check = False
    user_types = AttorneyUserType.objects.all()
    userprofile = None
    template = None
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
        
        
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        
        check = True

    if check:
        users = AttorneyStaff.objects.filter(created_by=userprofile.created_by)
        userprofile = userprofile.created_by
    else:
        users = AttorneyStaff.objects.filter(created_by=userprofile)
    try:
        template = HIPAADoc.objects.get(for_firm=userprofile)
    except:
        pass
    pages = Page.objects.all()     
    bank_accounts = BankAccounts.objects.filter(firm=userprofile)
    check_types = ChequeType.objects.all()
    # attachBankCheques = AttachBankCheque.objects.filter(firm=userprofile)

    # temp_check_types = []
    # index = 1
    # for check_type in check_types:
    #     temp = check_type.bankaccounts_set.all()
    #     print(temp)
        # for x in bank_accounts:
        #     if check_type in x.check_types.all():
        #         temp = x
        #         break
        
    #     temp_check_types.append({
    #                 'index':index,
    #                 'check_type':check_type,
    #                 'bank_account':temp
    #             })
    #     index += 1
    # print(temp_check_types)
    temp_bank_accounts = []
    index = 1
    for x in bank_accounts:
        str1 = ''
        for xx in x.check_types.all():
            str1 += xx.name
            str1 += ', '
        
        temp_bank_accounts.append({
            'index': index,
            'bank_account': x,
            'check_types':str1[:-2]
        })
        index += 1
    print(temp_bank_accounts)
    firm_users = AttorneyStaff.objects.filter(created_by=userprofile)
    statuses = Status.objects.all()
    context = {
        'userprofile': userprofile,
        'users': users,
        'user_types':user_types,
        'pages':pages,
        'bank_accounts':bank_accounts,
        'check_types':check_types,
        'temp_bank_accounts':temp_bank_accounts,
        'template':template,
        'firm_users':firm_users,
        'statuses': statuses
    }
    return render(request, 'BP/firm-setting.html', context)

def flaggedcases(request, client_id, case_id):
    flaggedPages = FlaggedPage.objects.all()
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
        
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)


    context = {
        'flaggedPages':flaggedPages,
        'client':client,
        'case':case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/flagged-cases.html', context)

def requestCheque(request, case_id):
    case = Case.objects.get(pk=case_id)
    userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
    if request.method == 'POST':
        incident_id = request.POST.get('request_record_id')
        cheque_type = request.POST.get('request_cheque_type')
        cheque_number = request.POST.get('request_check_number')
        memo = request.POST.get('request_memo')
        cost = request.POST.get('request_cost')
        cheque_type = ChequeType.objects.get(name=cheque_type)
        incident = IncidentReport.objects.get(pk=int(incident_id))

        check = Check.objects.create(cheque_number=cheque_number, amount=cost, payee=incident.payee, memo=memo, cheque_type=cheque_type, created_by=userprofile, for_case=incident.for_case)
        incident.cheque = check
        incident.save()


    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editbpAccounting(request):
    if request.method == 'POST':
        record_id = request.POST.get('record_id1')
        check = Check.objects.get(pk=int(record_id))
        cheque_number = request.POST.get('cheque_number')
        typex = request.POST.get('type')
        if typex == 'Paid':
            cleared_date = request.POST.get('cleared_date')
            check.cleared_date = cleared_date
            check.save()
        elif typex == 'Requested':
            check_date = request.POST.get('check_date')
            check.cheque_date = check_date
            check.save()
        check.cheque_number = cheque_number
        check.save()
        return redirect('bp-bpAccounting')

def markUserIntake(request, attorney_staff_id):
    user = AttorneyStaff.objects.get(pk=int(attorney_staff_id))
    if request.method == 'POST':
        intake = request.POST.get('intake')
        print(intake)
        if intake == 'on':
            user.isIntake = True
        else:
            user.isIntake = False
        user.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def markAccountingPermission(request, attorney_staff_id):
    user = AttorneyStaff.objects.get(pk=int(attorney_staff_id))
    if request.method == 'POST':
        permission_type = request.POST.get('permission_type')
        if permission_type == 'Accounting Permission':
            accounting_permission = request.POST.get('accounting_permission')
            print(accounting_permission)
            if accounting_permission == 'on':
                user.accounting_permission = 'True'
                user.save()
            else:
                user.accounting_permission = 'False'
                user.save()
        elif permission_type == 'Accounting Admin Permission':
            accounting_admin_permission = request.POST.get('accounting_admin_permission')
            print(accounting_admin_permission)
            if accounting_admin_permission == 'on':
                user.accounting_admin_permission = 'True'
                user.save()
            else:
                user.accounting_admin_permission = 'False'
                user.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addBankAccount(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)

        
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        bank = request.POST.get('bank')
        account_name = request.POST.get('account_name')
        account_number = request.POST.get('account_number')
        bank = BankAccounts.objects.create(firm=userprofile, bank=bank, account_name=account_name, account_number=account_number)
        bank.save()
    return redirect('bp-firmsetting')

def attachCheckAccount(request):
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)

        
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    if request.method == 'POST':
        check_type_id = request.POST.get('check_type_id')
        bank_account = request.POST.get('bank_account')
        check_type = ChequeType.objects.get(pk=int(check_type_id))
        bank_account = BankAccounts.objects.get(pk=int(bank_account))
        # attachcheckaccount = AttachBankCheque.objects.create(firm=userprofile, check_type=check_type, bank_account=bank_account)
        # attachcheckaccount.save()
        bank_account.check_types.add(check_type)
        bank_account.save()

        firm_users = AttorneyStaff.objects.filter(created_by=userprofile)
        firm_users_ids = []
        for firm_user in firm_users:
            firm_users_ids.append(firm_user.id)
        print(firm_users_ids)

        checks = Check.objects.filter(created_by__in=firm_users_ids, cheque_type=check_type)
        for check in checks:
            check.bank_account=bank_account
            check.save()
    return redirect('bp-firmsetting')


def bpAccounting(request):
    permission = False
    cheque_type = 'Requested'

    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
        permission = True

        
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        if userprofile.accounting_permission == 'True':
            permission = True
        userprofile = userprofile.created_by
    
    if request.method == 'POST':
        cheque_type = request.POST.get('name1')
    


    firm_users = AttorneyStaff.objects.filter(created_by=userprofile)
    firm_users_ids = []
    for firm_user in firm_users:
        firm_users_ids.append(firm_user.id)
    print(firm_users_ids)

    # temp_id = []
    # temp_id.append(userprofile.id)
    # clients = Client.objects.filter(created_by__in=temp_id)
    # temp_clients = []
    # for client in clients:
    #     temp_clients.append(client.id)
    # cases = Case.objects.filter(for_client__in=temp_clients)
    # temp_cases = []
    # for case in cases:
    #     temp_cases.append(case.id)
    if cheque_type == 'Requested':     
        requests = Check.objects.filter(created_by__in=firm_users_ids, cheque_number='')
    elif cheque_type == 'Paid':     
        requests = Check.objects.filter(~Q(cheque_number=''),cleared_date='',created_by__in=firm_users_ids)
    elif cheque_type == 'Cleared':     
        requests = Check.objects.filter(~Q(cheque_number=''),~Q(cleared_date=''),created_by__in=firm_users_ids)
    print(requests)
    
    context = {
        'requests':requests,
        'cheque_type':cheque_type,
        'permission':permission
    }
    return render(request, 'BP/bpAccounting.html', context)
        

def insurance(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
        
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    context = {
        'case':case,
        'client':client,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/insurance.html', context)

    

def incidentreport(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    templates = LetterTemplate.objects.filter(template_type='Incident Report')
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Incident Report')
        
    except:
        pass
    page = Page.objects.get(name='Incident Report')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    print(categories)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'templates':templates,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page': page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Incidentreport.html', context)

def addInjuryData(request, injury_id):
    injury = Injury.objects.get(pk=injury_id)
    case_providers = CaseProviders.objects.filter(for_case=injury.for_case)
    print(case_providers)
    if request.method == 'POST':
        
        note = request.POST.get('note')
        provider = request.POST.get('provider')
        case_provider = CaseProviders.objects.get(pk=int(provider))
        injury.provider = case_provider
        injury.note = note
        injury.save()
        print(provider)
        return redirect('bp-injuriessub', injury.for_client.id, injury.for_case.id)
    context = {
        'case_providers':case_providers
    }
    return render(request, 'BP/addInjuryData.html', context)


def addInjury(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        body_part = request.POST.get('body_part')
        injury = Injury.objects.create(body_part=body_part, for_client=client, for_case=case)
        injury.save()
    return redirect('bp-injuriessub', client.id, case.id)

def injuriessub(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Injury')
        
    except:
        pass
    injuries = Injury.objects.filter(for_client=client, for_case=case)
    page = Page.objects.get(name='Injury')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'injuries':injuries,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Injuriessub.html', context)

def injuries(request):
    flagPage = None
    
    context = {
        
    }
    return render(request, 'BP/injuries.html', context)

def lawfirmdirectory(request):
    return render(request, 'BP/Law-firm-directory.html')

def firmprofile(request):
    return render(request, 'BP/firmprofile.html')

def deleteIncidentReport(request):
    if request.method == 'POST':
        incident_id = request.POST.get('record_id2')
        incident = IncidentReport.objects.get(pk=int(incident_id))
        incident.delete()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editIncidentReport(request):
    if request.method == 'POST':
        incident_id = request.POST.get('record_id1')
        reporting_agency = request.POST.get('reporting_agency')
        office_first_name = request.POST.get('office_first_name')
        office_last_name = request.POST.get('office_last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        website = request.POST.get('website')
        phone = request.POST.get('phone')
        fax = request.POST.get('fax')
        report_number = request.POST.get('report_number')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        cost = request.POST.get('cost')
        check_number = request.POST.get('check_number')

        incident = IncidentReport.objects.get(pk=int(incident_id))
        incident.reporting_agency = reporting_agency
        incident.officer_first_name = office_first_name
        incident.officer_last_name = office_last_name
        incident.address1 = address1
        incident.address2 = address2
        incident.city = city
        incident.state = state
        incident.website = website
        incident.reporting_agency = reporting_agency
        incident.phone = phone
        incident.fax = fax
        incident.report_number = report_number
        incident.cost = cost
        incident.email = email
        incident.check_number = check_number
        incident.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found')) 


def addIncidentReport(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    if request.method == 'POST':
        reporting_agency = request.POST.get('reporting_agency')
        office_first_name = request.POST.get('office_first_name')
        office_last_name = request.POST.get('office_last_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        website = request.POST.get('website')
        phone = request.POST.get('phone')
        payee = request.POST.get('payee')
        fax = request.POST.get('fax')
        report_number = request.POST.get('report_number')
        email = request.POST.get('email')
        fax = request.POST.get('fax')
        cost = request.POST.get('cost')
        check_number = request.POST.get('check_number')


        incident_report = IncidentReport.objects.create(for_client=client, for_case=case, reporting_agency=reporting_agency,
                        address1=address1, address2=address2, city=city, state=state, phone=phone, 
                        report_number=report_number, email=email, fax=fax, officer_first_name=office_first_name, officer_last_name=office_last_name,
                        website=website, cost=cost, check_number=check_number, payee=payee 
                        )
        incident_report.save()
        return redirect('bp-incidentreport', client.id, case.id)
    context = {
        'client':client,
        'case':case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Incidentreport.html', context)

def addIncidentReportNote(request):
    if request.method == 'POST':
        description = request.POST.get('note_description')
        incident_id = request.POST.get('incident_id')
        incident_obj = IncidentReport.objects.get(pk=int(incident_id))
        note = IncidentNotes.objects.create(for_incident=incident_obj, description=description)
        note.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


def addCaseLoans(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    if request.method == 'POST':
        application_date = request.POST.get('application_date')
        loan_company = request.POST.get('loan_company')
        contact_name = request.POST.get('contact_name')
        phone = request.POST.get('phone')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        email = request.POST.get('email')
        loan_amount = request.POST.get('loan_amount')
        fees = request.POST.get('fees')
        status = request.POST.get('status')
        interest = request.POST.get('interest')
        amount_estimate = request.POST.get('amount_estimate')
        current_amount_verified = request.POST.get('current_amount_verified')
        date_verified = request.POST.get('date_verified')

        
        case_loan = CaseLoan.objects.create(for_client=client, for_case=case, application_date=application_date, loan_company=loan_company,
                    contact_name=contact_name, phone=phone, address1=address1, address2=address2, city=city, state=state,email=email,
                    loan_amount=loan_amount, fees=fees, status=status, interest=interest, amount_estimate=amount_estimate, zip_code=zip_code,
                    current_amount_verified=current_amount_verified, date_verified=date_verified
                    )
        case_loan.save()
        return redirect('bp-caseloan', client.id, case.id)
    context = {
        'client':client,
        'case':case,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/case-loan.html', context)


def addLitigation(request, client_id, case_id, litigation_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    litigation = None
    states = State.objects.all()
    counties = County.objects.all()
    try:
        litigation = Litigation.objects.get(pk=litigation_id)
    except:
        pass
    if request.method == 'POST':
        jurisdiction = request.POST.get('jurisdiction')
        court_name = request.POST.get('court_name')
        federal_court = request.POST.get('federal_court')
        judge_name = request.POST.get('judge_name')
        judge_contact = request.POST.get('judge_contact')
        department = request.POST.get('department')
        department_contact = request.POST.get('department_contact')
        court_address1 = request.POST.get('court_address1')
        court_address2 = request.POST.get('court_address2')
        court_address_city = request.POST.get('court_address_city')
        court_address_zip = request.POST.get('court_address_zip')

        
        state = request.POST.get('state')
        county = request.POST.get('county')
        case_number = request.POST.get('case_number')

        state = State.objects.get(pk=int(state))
        county = County.objects.get(pk=int(county))
        
        if litigation == None:
            litigation = Litigation.objects.create(for_client=client, for_case=case, jurisdiction=jurisdiction, court_name=court_name,
                            federal_court=federal_court, state=state, county=county, case_number=case_number, judge_contact=judge_contact,
                            judge_name=judge_name, department=department, court_address1=court_address1, court_address2=court_address2, court_address_city=court_address_city,
                            court_address_zip=court_address_zip, department_contact=department_contact
                         )
            litigation.save()
        else:
            litigation.jurisdiction = jurisdiction
            litigation.court_name = court_name
            litigation.judge_name = judge_name
            litigation.department = department
            litigation.department_contact = department_contact
            litigation.judge_contact = judge_contact
            litigation.court_address1 = court_address1
            litigation.court_address2 = court_address2
            litigation.court_address_city = court_address_city
            litigation.court_address_zip = court_address_zip
            litigation.federal_court = federal_court
            litigation.state = state
            litigation.county = county
            litigation.case_number = case_number
            
            litigation.save()
        return redirect('bp-litigation', client.id, case.id)
    context = {
        'client': client,
        'case':case,
        'litigation': litigation,
        'states': states,
        'counties': counties,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addLitigation.html', context)

def get_context_courtforms(client_id, case_id, litigation_id, original_form_context):
    litigation = Litigation.objects.get(pk=litigation_id)
    try:
        client = Client.objects.get(pk=int(client_id))
        client_address = ClientLocation.objects.get(added_by=client)
        case = Case.objects.get(pk=int(case_id))
        defendants = Defendant.objects.filter(for_client=client, for_case=case)
        attorney_location = AttorneyLocation.objects.filter(added_by=client.created_by)[0]
        firmuser = case.firm_users.all()[0]
        address = client_address.address + ' ' + client_address.address2 + ' ' + client_address.state + client_address.post_code
        
    except:
        pass
    current_date = datetime.datetime.today().strftime('%m/%d/%Y')
    variables = Variables.objects.all()
    print('this is the defendant',defendants[0].first_name)
    context = {}
    for variable in variables:
        try:
            context[variable.name] = eval(variable.value)
        except:
            pass
    for x in original_form_context:
        for key in x:
            context[key] = x[key]
    print(context)
    return context

def from_template_courtforms(template, client_id, case_id, litigation_id, original_form_context):
    target_file = StringIO()

    template = DocxTemplate(template)
    context = get_context_courtforms(client_id, case_id, litigation_id, original_form_context) 
    print(context)  # adds the InlineImage object to the context
    print('hehehe')
    target_file = BytesIO()
    template.render(context)
    template.save(target_file)
    return target_file


def downloadCourtForm(request, client_id, case_id, litigation_id, form_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    original_form_context = []
    court_form = CourtForms.objects.get(pk=form_id)
    if request.method == 'POST':
        csv_file = court_form.key
        data_set = csv_file.read().decode('utf-8-sig')
        io_string = io.StringIO(data_set)
        csvreader = csv.reader(io_string, delimiter=',', quotechar='"')
        S = 15

        for column in csvreader:
            if column[0] != '':
                checkbox = request.POST.get(column[0])
                if checkbox == 'on':
                    checkbox = 'X'
                else:
                    checkbox = ''
                
                original_form_context.append({
                    column[0]: checkbox,
                })
            if column[2] != '':
                field = request.POST.get(column[2])
                original_form_context.append({
                    column[2]: field,   
                })
        

        template = court_form.form
        file_path = template.url
        print(file_path)
        print('hello')
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = base_dir + file_path
        thefile = file_path
        filename = os.path.basename(thefile)
        print('this is the document url: ', thefile)
        document = from_template_courtforms(thefile, client.id, case.id, litigation_id, original_form_context)
        document.seek(0)
        print(document)
    
        response = HttpResponse(content=document)
        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response['Content-Disposition'] = 'attachment; filename="%s.docx"' \
                                        % 'whatever'
        return response
    return redirect('bp-addCourtForms', client.id, case.id, litigation_id)


def addCourtForms(request, client_id, case_id, litigation_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    litigation = Litigation.objects.get(pk=litigation_id)
    temp_form_context = None
    forms = CourtForms.objects.filter(for_state=litigation.state, for_county=litigation.county)
    form_id = -1
    if request.method == 'POST':
        form = request.POST.get('form')
        court_form = CourtForms.objects.get(pk=int(form))
        csv_file = court_form.key
        data_set = csv_file.read().decode('utf-8-sig')
        temp_form_context = []
        io_string = io.StringIO(data_set)
        form_id = int(form)
        csvreader = csv.reader(io_string, delimiter=',', quotechar='"')
        S = 15

        for column in csvreader:
          
            temp_form_context.append({
                'checkbox': column[0],
                'text': column[1],
                'field': column[2]
            })
    
    context = {
        'case':case,
        'client':client,
        'forms':forms,
        'temp_form_context':temp_form_context,
        'form_id': form_id,
        'litigation':litigation,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/addCourtForms.html', context)

# def generateForm(request, client_id, case_id, litigation_id):
#     temp_form_context = []
#     counter = 0
#     client = Client.objects.get(pk=client_id)
#     case = Case.objects.get(pk=case_id)
#     if request.method == 'POST':
#         forms = request.POST.get('forms')
#         court_form = CourtForms.objects.get(pk=int(forms))
#         csv_file = court_form.key
#         data_set = csv_file.read().decode('utf-8-sig')

#         io_string = io.StringIO(data_set)
        
#         csvreader = csv.reader(io_string, delimiter=',', quotechar='"')
#         S = 15
#         provider = None
        
#         for column in csvreader:
#             counter += 1
#             print(column)
#             temp_form_context.append({
#                 'checkbox': column[0],
#                 'text': column[1],
#                 'field': column[2]
#             })
#     print(temp_form_context)
#     context = {
#         'case':case,
#         'client':client,
#         'temp_form_context': temp_form_context,
#         'counter':counter,

#     }
#     return render(request, 'BP/addCourtForms.html', context)

def litigation(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    litigation = None
    try:
        litigation = Litigation.objects.get(for_client=client, for_case=case)
    except:
        pass
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Litigation')
        
    except:
        pass
    page = Page.objects.get(name='Litigation')
    litigation_details = LitigationDetails.objects.filter(for_client=client, for_case=case)
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'litigation':litigation,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'litigation_details':litigation_details,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Litigation.html', context)

def calculateGaps(request, case_id):
    case = Case.objects.get(pk=case_id)
    client_providers = CaseProviders.objects.filter(for_case=case)
    
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found')) 
             




def medicalcollapse(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client_id)
    case = Case.objects.get(pk=case_id)

            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    templates = LetterTemplate.objects.filter(template_type='Medical Provider')
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Medical Treatment')
        
    except:
        pass
    client_providers = CaseProviders.objects.filter(for_case=case)
    
    tf_treatment_dates = TFTreatmentDate.objects.filter(for_case=case)
    tf_accounting = TFAccounting.objects.filter(for_case=case)
    accounting_exists = []
    for client_provider in client_providers:
        temp_check = False
        try:
            q = TFAccounting.objects.get(for_case_provider=client_provider)
            temp_check = True
        except:
            pass
        
        accounting_exists.append({
            'case_provider':client_provider,
            'check':temp_check
        })
        
    days = 100000
    days_check = False
    treatment_gaps = []
    treatment_gap = None
    if request.method == 'POST':
        timeframe = request.POST.get('timeFrame')
        if timeframe == '1 week':
            days = 7
        elif timeframe == '2 weeks':
            days = 14
        elif timeframe == '3 weeks':
            days = 21
        elif timeframe == '30 days':
            days = 30
        elif timeframe == '60 days':
            days = 60
        elif timeframe == '90 days':
            days = 90
        elif timeframe == '180 days':
            days = 180
        elif timeframe == '1 year':
            days = 365
        else:
            days_check = True
    print(client_providers)
    for client_provider in client_providers:
        treatment_dates = list(TreatmentDates.objects.filter(for_provider=client_provider))
        print(treatment_dates)
        gap_days = -1
        # try:
        #     treatment_gap = TreatmentGap.objects.get(second_date=treatment_dates[0].date, for_case_provider=client_provider)
        #     gap_days = treatment_gap.days
        # except:

        #     d1 = dt.strptime(case.incident_date, "%Y-%m-%d")
        #     d2 = dt.strptime(treatment_dates[0].date, "%Y-%m-%d")
        #     gap_days = int(abs((d2 - d1).days))
        #     print(gap_days)
        #     doc = Doc.objects.create(for_client=case.for_client, for_case=case, page_name='Medical Collapse', document_no='Treatment Gap')
        #     treatment_gap = TreatmentGap.objects.create(for_case=case, first_date=case.incident_date, second_date=treatment_dates[0].date, days=gap_days, doc=doc, for_case_provider=client_provider)
        # treatment_gaps.append({
        #         'treatment_date': treatment_dates[0],
        #         'client_provider':client_provider,
        #         'gap':False
        #     })
        # if gap_days > days:
        #     treatment_gaps.append({
        #         'treatment_date': treatment_gap,
        #         'client_provider':client_provider,
        #         'gap':True
        #         })
        for i in range(len(treatment_dates)-1):
            gap_days = -1
            treatment_gap = None
            try:
                treatment_gap = TreatmentGap.objects.get(first_date=treatment_dates[i].date, second_date=treatment_dates[i+1].date, for_case_provider=client_provider)
                gap_days = treatment_gap.days
            except:
                d1 = dt.strptime(treatment_dates[i].date, "%Y-%m-%d")
                d2 = dt.strptime(treatment_dates[i+1].date, "%Y-%m-%d")
                gap_days = int(abs((d2 - d1).days))
                print(gap_days)
                doc = Doc.objects.create(for_client=case.for_client, for_case=case, page_name='Medical Collapse', document_no='Treatment Gap')
                treatment_gap = TreatmentGap.objects.create(for_case=case, first_date=treatment_dates[i].date, second_date=treatment_dates[i+1].date, days=gap_days, doc=doc, for_case_provider=client_provider)
                treatment_gap.save()
            treatment_gaps.append({
                'treatment_date': treatment_dates[i],
                'client_provider':client_provider,
                'gap':False
            })
            if gap_days > days and not days_check:
                treatment_gaps.append({
                    'treatment_date': treatment_gap,
                    'client_provider':client_provider,
                    'gap':True
                 })


        if len(treatment_dates) > 0:  
            treatment_gaps.append({
                'treatment_date': treatment_dates[-1],
                'client_provider':client_provider,
                'gap':False
            })
    print(treatment_gaps)

    page = Page.objects.get(name='Medical Treatment')
    final_checklist = []
    overall_checklist = []
    overall_checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_panelchecklists = 0
    checklist_panelpercentage = {}
    total_marked = 0
    total_panelmarked = {}
    for checklist in overall_checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                overall_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            overall_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
        
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    checklists = PanelCheckList.objects.filter(panel_name=page)
    total_panelchecklists = PanelCheckList.objects.filter(panel_name=page).count()
    for client_provider in client_providers:
        panel_case_checklists = PanelCaseChecklist.objects.filter(for_case=case, for_client=client, for_provider=client_provider)
        count = 0
        for checklist in checklists:
            check = False
            
            for panel_case_checklist in panel_case_checklists:
                if checklist.id == panel_case_checklist.checklist.id:
                    check = True
                    final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':panel_case_checklist.id,
                        'name': checklist.name,
                        
                        'status': True
                    })
                    count += 1
                    
            if not check:
                final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':-1,
                        'name': checklist.name,
                        'status': False,
                    })
            total_panelmarked[client_provider.id] = count
        try:
            checklist_panelpercentage[client_provider.id] = int((total_panelmarked[client_provider.id] * 100)/total_panelchecklists)
        except:
            checklist_panelpercentage[client_provider.id] = 0
    
    
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    print(total_panelmarked)
    print("\n", checklist_panelpercentage)
    context = {
        'client':client,
        'case':case,
        'client_address': address,
        'client_providers':client_providers,
        'flagPage':flagPage,
        'templates':templates,
        'checklist_percentage':checklist_percentage,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'final_checklist':final_checklist,
        'overall_checklist':overall_checklist, 
        'checklist_panelpercentage':checklist_panelpercentage,
        'total_panelmarked':total_panelmarked,
        'total_panelchecklists':total_panelchecklists, 
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users, 
        'tf_accounting':tf_accounting,
        'tf_treatment_dates':tf_treatment_dates,
        'accounting_exists':accounting_exists,
        'treatment_gaps':treatment_gaps,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Medical-collapse.html', context)

def medicalmin(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    client_providers = CaseProviders.objects.filter(for_case=case)
    context = {
        'client':client,
        'case':case,
        'client_providers':client_providers,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
        
    }
    return render(request, 'BP/Medical-min.html', context)

def medicalproviders(request):
    return render(request, 'BP/Medical-providers.html')

def deleteTreatmentNote(request):
    if request.method == 'POST':
        treatment_note_id = request.POST.get('treatment_date_id1')
        treatment_note = TreatmentDates.objects.get(pk=int(treatment_note_id))
        treatment_note.delete()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))  


def addTreatmentNotes(request, client_id, case_id):
    
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    treatment_note = None
    
    if request.method == 'POST':
        treatment_note_id = request.POST.get('treatment_date_id1')
        provider_id = request.POST.get('case_provider_id1')
        try:
            treatment_note = TreatmentDates.objects.get(pk=int(treatment_note_id))
        except:
            pass
        description = request.POST.get('treatment_note1')
        date = request.POST.get('treatment_date1')
        case_provider = CaseProviders.objects.get(pk=int(provider_id))
        if treatment_note == None:
            doc = Doc.objects.create(for_client=client, for_case=case, document_no='Document')
            doc.save()
            note = TreatmentDates.objects.create(for_provider=case_provider, description=description, date=date, document=doc)
            note.save()
            
        else:
            treatment_note.description = description
            treatment_note.date = date
            treatment_note.save()


        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))  
    
    context = {
        'client_id':client_id,
        'case_id':case_id,
        'treatment_note':treatment_note,
        'case_provider':case_provider,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }

    return render(request, 'BP/addTreatmentNotes.html', context)

def addVisits(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
   
    case = Case.objects.get(pk=case_id)
    
    if request.method == 'POST':
        visits = request.POST.get('visits')
        first_date = request.POST.get('first_date')
        second_date = request.POST.get('second_date')
        case_provider = request.POST.get('case_provider')
        if first_date == '':
            first_date = '_/_/_'
        if second_date == '':
            second_date = '_/_/_'
        if visits == '':
            visits = '__'
        client_provider = CaseProviders.objects.get(pk=int(case_provider))
        client_provider.visits = visits
        client_provider.first_date = first_date
        client_provider.second_date = second_date
        client_provider.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

    


def copyTFTreatmentDates(request):
    if request.method == 'POST':
        case_provider_id = request.POST.get('case_provider_id1')
        treatment_date_id = request.POST.get('treatment_date_id')
        case_provider = CaseProviders.objects.get(pk=int(case_provider_id))
        tf_treatment_date = TFTreatmentDate.objects.get(pk=int(treatment_date_id))
        case_provider.first_date = tf_treatment_date.first_date
        case_provider.second_date = tf_treatment_date.second_date
        case_provider.visits = tf_treatment_date.visits
        case_provider.save()
    
    
        index = int(case_provider.visits)
        case = case_provider.for_case
        doc = Doc.objects.create(for_client=case.for_client, for_case=case, document_no='Document')
        doc.save()
        date = TreatmentDates.objects.create(for_provider=case_provider, date=case_provider.first_date, document=doc)
        date.save()
        x_date = case_provider.first_date
        temp_date = datetime.datetime.strptime(x_date, '%Y-%m-%d')
        

        
        
        for i in range(1,index-1):
            doc = Doc.objects.create(for_client=case.for_client, for_case=case, document_no='Document')
            doc.save()
            
            current_date = temp_date + datetime.timedelta(days=1)
            current_date = str(current_date.date())

            temp_date = datetime.datetime.strptime(current_date, '%Y-%m-%d')
            date = TreatmentDates.objects.create(for_provider=case_provider, document=doc, date=current_date)
            date.save()
        doc = Doc.objects.create(for_client=case.for_client, for_case=case, document_no='Document')
        doc.save()   
        date = TreatmentDates.objects.create(for_provider=case_provider, date=case_provider.second_date, document=doc)
        date.save()



    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editAccounting(request):
    print('hello')
    if request.method == 'POST':
        case_provider_id = request.POST.get('case_provider_id')
        
        original = request.POST.get('original')
        hi_paid = request.POST.get('hi_paid')
        mp_paid = request.POST.get('mp_paid')
        reduction = request.POST.get('reduction')
        hi_reduction = request.POST.get('hi_reduction')
        case_provider = CaseProviders.objects.get(pk=int(case_provider_id))
       
        bp_accounting = None
        
        bp_accounting = BPAccounting.objects.get(for_case_provider=case_provider)
       

        final_amount = float(original) - (float(hi_paid) + float(mp_paid) + float(reduction) + float(hi_reduction))
        bp_accounting.original = float(original)
        bp_accounting.hi_paid = float(hi_paid)
        bp_accounting.mp_paid = float(mp_paid)
        bp_accounting.hi_reduction = float(hi_reduction)
        bp_accounting.reduction = float(reduction)
        final_amount = '{:.2f}'.format(final_amount)
        bp_accounting.final = float(final_amount)
        bp_accounting.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def medicaltreatment(request, client_id, case_id):
    print('CLient Id in medical', client_id)
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client_id)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    templates = LetterTemplate.objects.filter(template_type='Medical Provider')
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Medical Treatment')
        
    except:
        pass
    client_providers = CaseProviders.objects.filter(for_case=case)
    case_provider_medical = ''
    try:
        case_provider_medical = CaseProviders.objects.get(for_case = case , for_case__for_client = client)
        print('CLient Provider __----------', case_provider_medical)
    except:
        pass
    
    tf_treatment_dates = TFTreatmentDate.objects.filter(for_case=case)
    tf_accounting = TFAccounting.objects.filter(for_case=case)
    accounting_exists = []
    for client_provider in client_providers:
        temp_check = False
        try:
            q = TFAccounting.objects.get(for_case_provider=client_provider)
            temp_check = True
        except:
            pass
        
        accounting_exists.append({
            'case_provider':client_provider,
            'check':temp_check
        })
        


    page = Page.objects.get(name='Medical Treatment')
    final_checklist = []
    overall_checklist = []
    overall_checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_panelchecklists = 0
    checklist_panelpercentage = {}
    total_marked = 0
    total_panelmarked = {}
    for checklist in overall_checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                overall_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            overall_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
        
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    checklists = PanelCheckList.objects.filter(panel_name=page)
    total_panelchecklists = PanelCheckList.objects.filter(panel_name=page).count()
    for client_provider in client_providers:
        panel_case_checklists = PanelCaseChecklist.objects.filter(for_case=case, for_client=client, for_provider=client_provider)
        count = 0
        for checklist in checklists:
            check = False
            
            for panel_case_checklist in panel_case_checklists:
                if checklist.id == panel_case_checklist.checklist.id:
                    check = True
                    final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':panel_case_checklist.id,
                        'name': checklist.name,
                        
                        'status': True
                    })
                    count += 1
                    
            if not check:
                final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':-1,
                        'name': checklist.name,
                        'status': False,
                    })
            total_panelmarked[client_provider.id] = count
        try:
            checklist_panelpercentage[client_provider.id] = int((total_panelmarked[client_provider.id] * 100)/total_panelchecklists)
        except:
            checklist_panelpercentage[client_provider.id] = 0
    
    
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    print(total_panelmarked)
    print("\n", checklist_panelpercentage)
    context = {
        'client':client,
        'case':case,
        'client_address': address,
        'client_providers':client_providers,
        'flagPage':flagPage,
        'templates':templates,
        'checklist_percentage':checklist_percentage,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'final_checklist':final_checklist,
        'overall_checklist':overall_checklist, 
        'checklist_panelpercentage':checklist_panelpercentage,
        'total_panelmarked':total_panelmarked,
        'total_panelchecklists':total_panelchecklists, 
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users, 
        'tf_accounting':tf_accounting,
        'tf_treatment_dates':tf_treatment_dates,
        'accounting_exists':accounting_exists,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos, 
        'case_provider_medical':case_provider_medical
    }
    return render(request, 'BP/Medical-treatment.html', context)

def note(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
            
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Note')
        
    except:
        pass
    page = Page.objects.get(name='Notes')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/note.html', context)

def addOtherPartyInsurance(request):
    if request.method == 'POST':
        other_party_id = request.POST.get('other_party')
        insurance_type = request.POST.get('insurance_type')
        policy_number = request.POST.get('policy_number')
        claim_number = request.POST.get('claim_number')
        company_name = request.POST.get('company_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        fax = request.POST.get('fax')
        email = request.POST.get('email')

        contact = Contact.objects.create(address1=address1, address2=address2, email=email, phone_number=phone, city=city, state=state, fax=fax, zip=zip)
        contact.save()
        company = Company.objects.create(company_name=company_name, contact=contact)
        company.save()
        insurance_type = InsuranceType.objects.get(pk=int(insurance_type))
        insurance = Insurance.objects.create(company=company, insurance_type=insurance_type, policy_number=policy_number, claim_number=claim_number)
        other_party = OtherParty.objects.get(pk=int(other_party_id))
        other_party.other_party_insurance.add(insurance)
        other_party.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addWitnessInsurance(request):
    if request.method == 'POST':
        witness_id = request.POST.get('witness')
        insurance_type = request.POST.get('insurance_type')
        policy_number = request.POST.get('policy_number')
        claim_number = request.POST.get('claim_number')
        company_name = request.POST.get('company_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        fax = request.POST.get('fax')
        email = request.POST.get('email')

        contact = Contact.objects.create(address1=address1, address2=address2, email=email, phone_number=phone, city=city, state=state, fax=fax, zip=zip)
        contact.save()
        company = Company.objects.create(company_name=company_name, contact=contact)
        company.save()
        insurance_type = InsuranceType.objects.get(pk=int(insurance_type))
        insurance = Insurance.objects.create(company=company, insurance_type=insurance_type, policy_number=policy_number, claim_number=claim_number)
        witness = Witness.objects.get(pk=int(witness_id))
        witness.witness_insurance.add(insurance)
        witness.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


def addDefendantInsurance(request):
    if request.method == 'POST':
        defendant_id = request.POST.get('defendant')
        insurance_type = request.POST.get('insurance_type')
        policy_number = request.POST.get('policy_number')
        claim_number = request.POST.get('claim_number')
        company_name = request.POST.get('company_name')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        fax = request.POST.get('fax')
        email = request.POST.get('email')

        contact = Contact.objects.create(address1=address1, address2=address2, email=email, phone_number=phone, city=city, state=state, fax=fax, zip=zip)
        contact.save()
        company = Company.objects.create(company_name=company_name, contact=contact)
        company.save()
        insurance_type = InsuranceType.objects.get(pk=int(insurance_type))
       
        insurance = Insurance.objects.create(company=company, insurance_type=insurance_type, policy_number=policy_number, claim_number=claim_number)
        defendant = Defendant.objects.get(pk=int(defendant_id))
        defendant.liability_insurance_id.add(insurance)
        defendant.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))



def otherparties(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    otherparties = OtherParty.objects.filter(for_client=client, for_case=case)
    insurance_types = InsuranceType.objects.all()
    templates = LetterTemplate.objects.filter(template_type='Other Parties')
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Other Party')
        
    except:
        pass
    page = Page.objects.get(name='Other Parties')
    final_checklist = []
    overall_checklist = []
    overall_checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_panelchecklists = 0
    checklist_panelpercentage = {}
    total_marked = 0
    total_panelmarked = {}
    for checklist in overall_checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                overall_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            overall_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
        
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    checklists = PanelCheckList.objects.filter(panel_name=page)
    total_panelchecklists = PanelCheckList.objects.filter(panel_name=page).count()
    for client_provider in otherparties:
        panel_case_checklists = PanelCaseChecklist.objects.filter(for_case=case, for_client=client, for_otherparty=client_provider)
        count = 0
        for checklist in checklists:
            check = False
            
            for panel_case_checklist in panel_case_checklists:
                if checklist.id == panel_case_checklist.checklist.id:
                    check = True
                    final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':panel_case_checklist.id,
                        'name': checklist.name,
                        
                        'status': True
                    })
                    count += 1
                    
            if not check:
                final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':-1,
                        'name': checklist.name,
                        'status': False,
                    })
            total_panelmarked[client_provider.id] = count
        try:
            checklist_panelpercentage[client_provider.id] = int((total_panelmarked[client_provider.id] * 100)/total_panelchecklists)
        except:
            checklist_panelpercentage[client_provider.id] = 0
    
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'otherparties':otherparties,
        'templates':templates,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,

        'overall_checklist':overall_checklist, 
        'checklist_panelpercentage':checklist_panelpercentage,
        'total_panelmarked':total_panelmarked,
        'total_panelchecklists':total_panelchecklists,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'insurance_types':insurance_types,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Other-Parties.html', context)

def photo(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Photo')
        
    except:
        pass
    page = Page.objects.get(name='Photo')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Photo.html', context)

def recordings(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Recording')
        
    except:
        pass
    page = Page.objects.get(name='Recordings')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Recordings.html', context)

def searchcity(request):
    return render(request, 'BP/serach-city.html')

def advanceSearch(request):
    context = {}
    
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
        
        
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    page = Page.objects.get(name='Search Page')
    if request.method == 'POST':
        name = request.POST.get('name')
        search_category = request.POST.get('search_category')

        if search_category == 'Client':

            clients = Client.objects.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            clients = clients.filter(created_by=userprofile)
            print('In Client -- ', name)
            temp_client = []
            index = 0
            for client in clients:
                
                cases = Case.objects.filter(for_client=client)
                for case in cases:
                    index += 1
                    temp_client.append({
                        'case':case,
                        'index': index,
                        'check':True,
                    })
            context = {
                'page':page,
                'name':name,
                'clients': temp_client
            }
            return render(request, 'BP/serach-client.html', context)
        elif search_category == 'Defendant':
            print('In Defendant -- ', name)
            defendants = Defendant.objects.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            print(defendants)
            context = {
                'page':page,
                'name':name,
                'defendants': defendants
            }
            return render(request, 'BP/serach-defendant.html', context)
        elif search_category == 'Witness':
            print('In Witness -- ', name)
            witnesses = Witness.objects.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            print(witnesses)
            context = {
                'page':page,
                'name':name,
                'witnesses': witnesses
            }
            return render(request, 'BP/serach-witness.html', context)
        elif search_category == 'OtherParty':
            print('In Other Party -- ', name)
            other_parties = OtherParty.objects.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            print(other_parties)
            context = {
                'page':page,
                'name':name,
                'other_parties': other_parties
            }
            return render(request, 'BP/serach-other-party.html', context)
        elif search_category == 'Note':
            print('In Note -- ', name)
            
            notes = Notes.objects.filter(Q(description__icontains=name))
            print(notes)
            temp_notes = []
            index = 0
            for note in notes:
                description = str(note.description)
                description = description.replace(name, '<b>'+name+'</b>')
                index += 1
                print(description)
                
                temp_notes.append({
                    'note':note,
                    'description': description,
                    'index':index
                })
            context = {
                'page':page,
                'name':name,
                'notes': temp_notes
            }
            return render(request, 'BP/serach-note.html', context)
        elif search_category == 'City':
            print('In City -- ', name)
            locations = ClientLocation.objects.filter(Q(city__icontains=name))
            print(locations)
            temp_locations = []
            index = 0
            for location in locations:
                cases = Case.objects.filter(for_client=location.added_by)
                for case in cases:
                    index += 1
                    temp_locations.append({
                        'case':case,
                        'index':index,
                        'city':location.city,
                        'state':location.state
                    })

            context = {
                'name':name,
                'locations': temp_locations
            }
            return render(request, 'BP/serach-city.html', context)
        elif search_category == 'Provider':
            print('In City -- ', name)
            providers = CaseProviders.objects.filter(provider__providerprofile__office_name__icontains=name)
            print(providers)
            context = {
                'name':name,
                'providers': providers
            }
            return render(request, 'BP/serach-provider.html', context)
    return redirect('bp-searchclient')
def searchclient(request):
    name = ''
    temp_client = []
    clients = None
    page = Page.objects.get(name='Search Page')
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
        
        
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        userprofile = userprofile.created_by
    
    if request.method == "POST":
        name = request.POST.get('name')
        check = request.POST.get('check')
        if check == 'True':
            clients = Client.objects.filter(last_name__startswith=name)
            
        else:
            clients = Client.objects.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            clients = clients.filter(created_by=userprofile)
        
        index = 0
        for client in clients:
            
            cases = Case.objects.filter(for_client=client)
            for case in cases:
                index += 1
                temp_client.append({
                    'case':case,
                    'index': index,
                    
                })
    context = {
        'name':name,
        'clients': temp_client,
        'page':page
    }

    return render(request, 'BP/serach-client.html', context)

def searchdefendant(request):
    return render(request, 'BP/serach-defendant.html')

def searchnote(request):
    return render(request, 'BP/serach-note.html')

def searchotherparty(request):
    return render(request, 'BP/serach-other-party.html')

def searchprovider(request):
    return render(request, 'BP/serach-provider.html')

def searchwitness(request):
    return render(request, 'BP/serach-witness.html')

def addOffer(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        check = request.POST.get('check')
        date = request.POST.get('date')
        note = request.POST.get('note')
        check_number = request.POST.get('check_number')
        amount = request.POST.get('amount')
        if not check_number:
            check_number = 0
        offer = None
        if check == 'False':
            offer = Offer.objects.create(for_client=client, for_case=case, date=date, note=note, check_number=check_number, 
                                        amount=amount
                                        )
        else:
            offer = Offer.objects.get(pk=int(check))
            offer.date = date
            offer.note = note
            offer.check_number = check_number
            offer.amount = amount
            
        offer.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addFees(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        check = request.POST.get('check')
        note = request.POST.get('note')
        check_number = request.POST.get('check_number')
        amount = request.POST.get('amount')
        final_amount = request.POST.get('final_amount')
        fee = None
        if check == 'False':
            fee = Fees.objects.create(for_client=client, for_case=case, note=note, check_number=check_number, 
                                        amount=amount, final_amount=final_amount
                                        )
        else:
            fee = Fees.objects.get(pk=int(check))
            fee.note = note
            fee.check_number = check_number
            fee.amount = amount
            fee.final_amount = final_amount
            
        fee.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addSettlementCosts(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        check = request.POST.get('check')
        date = request.POST.get('date')
        payee = request.POST.get('payee')
        check_number = request.POST.get('check_number')
        check_date = request.POST.get('check_date')
        final_amount = request.POST.get('final_amount')
        cost = None
        if check == 'False':
            cost = Costs.objects.create(for_client=client, for_case=case, date=date, payee=payee, check_number=check_number, 
                                        check_date=check_date, final_amount=final_amount
                                        )
        else:
            cost = Costs.objects.get(pk=int(check))
            cost.date = date
            cost.payee = payee
            cost.check_number = check_number
            cost.check_date = check_date
            cost.final_amount = final_amount
        cost.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def addClientProceeds(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        check = request.POST.get('check')
        name_on_check = request.POST.get('name_on_check')
        check_number = request.POST.get('check_number')
        check_date = request.POST.get('check_date')
        amount = request.POST.get('amount')
        cleared = request.POST.get('cleared')
        client_proceed = None
        if check == 'False':
            client_proceed = ClientProceeds.objects.create(for_client=client, for_case=case, check_number=check_number,
                                                            amount=amount, check_date=check_date, name_on_check=name_on_check,
                                                            cleared=cleared
                                                            )
        else:
            client_proceed = ClientProceeds.objects.get(pk=int(check))
            client_proceed.name_on_check = name_on_check
            client_proceed.check_number = check_number
            client_proceed.check_date = check_date
            client_proceed.amount = amount
            client_proceed.cleared = cleared
        client_proceed.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
        

def checkSettlementOffer(request, offer_id):
    offer = Offer.objects.get(pk=offer_id)
    offer.final_amount = 'True'
    offer.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editSettlementProviders(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        check = request.POST.get('check')
        amount = request.POST.get('amount')
        ins_paid = request.POST.get('ins_paid')
        write_off = request.POST.get('write_off')
        reduction = request.POST.get('reduction')
        # final_amount = request.POST.get('final_amount')
        check_number = request.POST.get('check_number')
        temp_amount = float(amount) - (float(ins_paid) + float(write_off) + float(reduction))
        provider = CaseProviders.objects.get(pk=int(check))
        provider.amount = amount
        provider.ins_paid = ins_paid
        provider.write_off = write_off
        provider.reduction = reduction
        provider.final_amount = temp_amount
        provider.check_number = check_number
        provider.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def editSettlementCaseLoans(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    if request.method == 'POST':
        check = request.POST.get('check')
        application_date = request.POST.get('application_date')
        current_amount = request.POST.get('current_amount')
        date_verified = request.POST.get('date_verified')
        final_amount = request.POST.get('final_amount')
        check_number = request.POST.get('check_number')

        loan = CaseLoan.objects.get(pk=int(check))
        loan.application_date = application_date
        loan.current_amount = current_amount
        loan.date_verified = date_verified
        loan.final_amount = final_amount
        loan.check_number = check_number
        loan.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


def removeSettlementRecord(request, panel_name):
    if request.method == 'POST':
        record_id = request.POST['record_id']
        if panel_name == 'Offer':
            offer = Offer.objects.get(pk=int(record_id))
            offer.delete()
        elif panel_name == 'Fees':
            fee = Fees.objects.get(pk=int(record_id))
            fee.delete()
        elif panel_name == 'Costs':
            cost = Costs.objects.get(pk=int(record_id))
            cost.delete()
        elif panel_name == 'Providers':
            provider = CaseProviders.objects.get(pk=int(record_id))
            provider.delete()
        elif panel_name == 'Loans':
            loan = CaseLoan.objects.get(pk=int(record_id))
            loan.delete()
        elif panel_name == 'Client Proceeds':
            client_proceed = ClientProceeds.objects.get(pk=int(record_id))
            client_proceed.delete()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

def settlement(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    offers = Offer.objects.filter(for_client=client, for_case=case)
    fees = Fees.objects.filter(for_client=client, for_case=case)
    costs = Costs.objects.filter(for_client=client, for_case=case)
    loans = CaseLoan.objects.filter(for_client=client, for_case=case)
    providers = CaseProviders.objects.filter(for_case=case)
    client_proceeds = ClientProceeds.objects.filter(for_client=client, for_case=case)
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Settlement')
        
    except:
        pass
    page = Page.objects.get(name='Settlement')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'offers':offers,
        'fees':fees,
        'costs':costs,
        'loans':loans,
        'providers':providers,
        'client_proceeds':client_proceeds,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Settlement.html', context)

def todo(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    todos = None
    print(request.user)
    try:
        profile = Firm.objects.get(user=request.user, account_type='Attorney')
        userprofile = Attorney.objects.get(attorneyprofile=profile)
        print(userprofile.user_type)
        todos = ToDo.objects.filter(for_client=client, for_case=case)
    except:
        userprofile = AttorneyStaff.objects.get(user=request.user, account_type='AttorneyStaff')
        todos = ToDo.objects.filter(for_client=client, for_case=case, todo_for=userprofile)
        userprofile = userprofile.created_by
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='To-Do')
        
    except:
        pass
    page = Page.objects.get(name='To-Do')
    final_checklist = []
    checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_marked = 0
    
    for checklist in checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                final_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            final_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'todos':todos,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/To-Do.html', context)

def totaldamages(request):
    return render(request, 'BP/total-damages.html')

def witnesses(request, client_id, case_id):
    client = Client.objects.get(pk=client_id)
    address = ClientLocation.objects.get(added_by=client)
    case = Case.objects.get(pk=case_id)
    
    current_todos = ToDo.objects.filter(for_case=case, status='Not Completed').count()
    case_statuses = Status.objects.all()
    case_stages = Stage.objects.all()

    recent_cases = None
    jsonDec = json.decoder.JSONDecoder()
    try:
        recent_cases = RecentCases.objects.get(user=request.user)
        
        case_ids = jsonDec.decode(recent_cases.case_ids)
        print(case_ids)
        if case.id in case_ids:
            case_ids.remove(case.id)
        if len(case_ids) == 9:
            case_ids[-1] = case.id
        else:
            case_ids.append(case.id)
        recent_cases.case_ids = json.dumps(case_ids)
        recent_cases.save()
        print('I am in')
    except:
        pass

    last_accessed_cases = []
    if recent_cases:
        case_ids = jsonDec.decode(recent_cases.case_ids)
        for case_id in reversed(case_ids):
            x = Case.objects.get(pk=int(case_id))
            last_accessed_cases.append(x)
    print(last_accessed_cases)
    current_case = last_accessed_cases[0]
    last_accessed_cases.pop(0)

    witnesses = Witness.objects.filter(for_client=client, for_case=case)
    insurance_types = InsuranceType.objects.all()
    templates = LetterTemplate.objects.filter(template_type='Witnesses')
    flagPage = None
    try:
        flagPage = FlaggedPage.objects.get(for_client=client, for_case=case, page_name='Witness')
        
    except:
        pass
    page = Page.objects.get(name='Witnesses')
    final_checklist = []
    overall_checklist = []
    overall_checklists = CheckList.objects.filter(page=page)
    case_checklists = CaseChecklist.objects.filter(for_case=case, for_client=client)
    total_checklists = 0
    total_panelchecklists = 0
    checklist_panelpercentage = {}
    total_marked = 0
    total_panelmarked = {}
    for checklist in overall_checklists:
        check = False
        total_checklists += 1
        for case_checklist in case_checklists:
            if checklist.id == case_checklist.checklist.id:
                print('hello world')
                check = True
                overall_checklist.append({
                    'id':checklist.id,
                    'case_checklist_id': case_checklist.id,
                    'name':checklist.name,
                    'status': True,
                })
                total_marked += 1
        if not check:    
            overall_checklist.append({
                        'id':checklist.id,
                        'name':checklist.name,
                        'case_checklist_id': -1,
                        'status': False,
                    })
        
    try:
        checklist_percentage = int((total_marked * 100)/total_checklists)
    except:
        checklist_percentage = 0
    checklists = PanelCheckList.objects.filter(panel_name=page)
    total_panelchecklists = PanelCheckList.objects.filter(panel_name=page).count()
    for client_provider in witnesses:
        panel_case_checklists = PanelCaseChecklist.objects.filter(for_case=case, for_client=client, for_witness=client_provider)
        count = 0
        for checklist in checklists:
            check = False
            
            for panel_case_checklist in panel_case_checklists:
                if checklist.id == panel_case_checklist.checklist.id:
                    check = True
                    final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':panel_case_checklist.id,
                        'name': checklist.name,
                        
                        'status': True
                    })
                    count += 1
                    
            if not check:
                final_checklist.append({
                        'id': checklist.id,
                        'provider':client_provider,
                        'panel_case_checklist':-1,
                        'name': checklist.name,
                        'status': False,
                    })
            total_panelmarked[client_provider.id] = count
        try:
            checklist_panelpercentage[client_provider.id] = int((total_panelmarked[client_provider.id] * 100)/total_panelchecklists)
        except:
            checklist_panelpercentage[client_provider.id] = 0
    
    print(final_checklist)
    case_users = case.firm_users.all()
    notes = Notes.objects.filter(for_client=client, for_case=case)
    categories = []
    pages = Page.objects.all()
    for temp_page in pages:
        if Notes.objects.filter(for_client=client, for_case=case, category=temp_page).count() >= 1:
            categories.append(temp_page.name)
    context = {
        'client':client,
        'case':case,
        'client_address':address,
        'witnesses':witnesses,
        'templates':templates,
        'flagPage':flagPage,
        'final_checklist':final_checklist,
        'total_marked':total_marked,
        'total_checklists':total_checklists,
        'checklist_percentage':checklist_percentage,

        'overall_checklist':overall_checklist, 
        'checklist_panelpercentage':checklist_panelpercentage,
        'total_panelmarked':total_panelmarked,
        'total_panelchecklists':total_panelchecklists,
        'pages':pages,
        'notes':notes,
        'categories':categories,
        'case_users':case_users,
        'page':page,
        'insurance_types':insurance_types,
        'case_statuses':case_statuses,
        'case_stages':case_stages,
        'current_case':current_case,
        'last_accessed_cases':last_accessed_cases,
        'current_todos':current_todos,
    }
    return render(request, 'BP/Witnesses.html', context)

def addNewEventsCalendar(request):
    if request.method == 'POST':
        case_id = request.POST.get('case_id')
        case = Case.objects.get(pk=int(case_id))
        event_type = request.POST.get('event_type')
        if event_type == 'Litigation Events':
            litigation_type = request.POST.get('litigation_type')
            description = request.POST.get('description')
            zoom_link = request.POST.get('zoom_link')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            if end_date == '':
                end_date = start_date

            litigation = LitigationDetails.objects.create(for_client=case.for_client, for_case=case, litigation_type=litigation_type,
                        description=description, zoom_link=zoom_link, date=start_date, time=start_time, end_time=end_time, end_date=end_date
                        )
            litigation.save()
        if event_type == 'ToDo Events':
            firm_user = request.POST.get('firm_user')
            due_date = request.POST.get('due_date')
            start_time = request.POST.get('start_time')
            note = request.POST.get('note')


            firm_user = AttorneyStaff.objects.get(pk=int(firm_user))

            todo = ToDo.objects.create(for_client=case.for_client, for_case=case, created_by=request.user,
                due_date=due_date, time=start_time, todo_for=firm_user, notes=note
                )
            todo.save()
        if event_type == 'Statute Events':
            statute_date = request.POST.get('statute_date')
            start_time = request.POST.get('start_time')
            statute_date = Statute.objects.create(for_client=case.for_client, for_case=case, statute_date=statute_date, time=start_time)
            statute_date.save()


        
    return redirect('bp-calendar')



def redirectCalendarEvent(request):
    case_id = request.GET.get('case_id')
    url = request.GET.get('url')
    temp_id = request.GET.get('id')
    title = request.GET.get('title')
    start = request.GET.get('start_date')
    start_time = request.GET.get('start_time')
    if title == 'To-Do':
        todo = ToDo.objects.get(pk=int(temp_id))
        todo.due_date = start
        todo.time = start_time
        todo.save()
    elif title == 'Statute':
        statute = Statute.objects.get(pk=int(temp_id))
        statute.statute_date = start
        statute.time = start_time
        statute.save()
    else:
        litigation = LitigationDetails.objects.get(pk=int(temp_id))
        litigation.date = start
        litigation.time = start_time
        litigation.save()

    data = {}
    return JsonResponse(data)

def updateStampedTemplate(request, doc_template_id):
    # jairo
    if request.method == 'POST':
        try:
            doc_template_instance = Doc_Template.objects.get(id=doc_template_id)
            form = Doc_Template_Update_Form(data=request.POST or None, files=request.FILES, instance=doc_template_instance)
            if form.is_valid():
                form.save()

            # messages.success(request, 'Template has been updated successfully')
        except Exception as e:
            print(e)
            # messages.error(request, 'Operation Failed! Please try Again.')

    return redirect('bp-firmsetting')