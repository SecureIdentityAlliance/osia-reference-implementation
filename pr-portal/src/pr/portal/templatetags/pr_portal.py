import datetime

from django import template

register = template.Library()

@register.filter('age')
def age(d):
    t = datetime.date.today()
    return (t.year - d.year) - int((t.month, t.day) < (d.month, d.day))
