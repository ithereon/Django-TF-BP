from .models import Specialty
import django_filters

class SpecialtyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Specialty
        fields = ['name']

