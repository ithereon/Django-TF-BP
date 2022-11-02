from django import template
register = template.Library()


def time_of_note(val):
    print(val)
    split_arr=val.time()
    return split_arr

register.filter('time_of_note', time_of_note)