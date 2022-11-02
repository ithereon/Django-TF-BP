from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']

class DocSerializer(serializers.ModelSerializer):
    upload = serializers.FileField()
    class Meta:
        model = Doc
        fields = ['id', 'for_client', 'for_case', 'upload', 'file_name', 'page_name', 'document_no', 'check', 'ocr_StatusChoices', 'ocr_tries', 'ocr_status', 'created', 'provider_documents']

class CaseStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStage
        fields = '__all__'

class ClientStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientStatus
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class FirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = '__all__'

class AttorneySerializer(serializers.ModelSerializer):
    attorneyprofile = FirmSerializer(many=False)
    perform_search = serializers.SerializerMethodField(method_name='perform_search_set')
    class Meta:
        model = Attorney
        fields = ['id', 'attorneyprofile', 'marketer_code', 'user_type', 'perform_search']
    
    def perform_search_set(self, attorney:Attorney):
        return "True"

class AttorneyStaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)
    class Meta:
        model = AttorneyStaff
        fields = ['id', 'user', 'phone_extension', 'user_type']

class ReportingAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportingAgency
        fields = '__all__'