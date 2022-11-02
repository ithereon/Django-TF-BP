from django import template
register = template.Library()


def date_of_note(val):
    print(val)
    split_arr=val.date()
    return split_arr

register.filter('date_of_note', date_of_note)