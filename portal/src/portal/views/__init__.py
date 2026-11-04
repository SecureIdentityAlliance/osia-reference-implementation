import os

def get_url(name, default):
    u = os.environ.get(name, default)
    u = u+'/' if u and u[-1]!='/' else u
    return u

def pr_url():
    return get_url('PR_URL', 'http://pr:8080/')

def uin_url():
    return get_url('UIN_URL', 'http://uin:8080/')

def abis_url():
    return get_url('ABIS_URL', 'http://abis:8080/')

