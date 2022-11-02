from rest_framework import serializers
from .models import *

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'color', 'radius', 'secondary_color']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['address', 'address2', 'city', 'state', 'post_code']

class TFDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = TFDoc
        fields = '__all__'
        