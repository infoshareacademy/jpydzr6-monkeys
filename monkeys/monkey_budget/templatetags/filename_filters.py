from django import template
import os

register = template.Library()

@register.filter
def endswith(value, arg):
    if not isinstance(value, str):
        return False
    if not isinstance(arg, str):
        return False
    return value.lower().endswith(arg.lower())

@register.filter
def basename(value):
    return os.path.basename(value)
