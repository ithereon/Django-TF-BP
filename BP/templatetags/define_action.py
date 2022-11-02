from django import template
register = template.Library()


def define(val):
    action=val
    return action

register.filter('define', define)