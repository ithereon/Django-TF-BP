import datetime
from django import template

register = template.Library()

import phonenumbers
@register.filter(name='phonenumber')
def phonenumber(value, country=None):
   return phonenumbers.parse(value, country)

