import os

from django.template.defaulttags import register

def get_url(name, default):
    u = os.environ.get(name, default)
    u = u+'/' if u and u[-1]!='/' else u
    return u

def enr_url():
    return get_url('ENROLLMENT_URL', 'http://enrollment:8080/')

def uin_url():
    return get_url('UIN_URL', 'http://uin:8080/')

def orch_url():
    return get_url('ORCHESTRATOR_URL', 'http://orchestrator:8080/')

def notif_url():
    return get_url('NOTIFICATION_URL', 'http://notification:8080/')

def pr_url():
    return get_url('PR_URL', 'http://pr:8080/')

def abis_url():
    return get_url('ABIS_URL', 'http://abis:8080/')

@register.filter(is_safe=True)
def in_env(value):
    if value in os.environ:
        return '1'
    return '0'

