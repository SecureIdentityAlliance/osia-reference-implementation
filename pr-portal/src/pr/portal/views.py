import logging
import os
import datetime
import random
import base64

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.template.defaulttags import register

import requests

def pr_url():
    return os.environ.get('PR_URL', 'http://localhost:8010')

def uin_url():
    return os.environ.get('UIN_URL', 'http://localhost:8020')

def abis_url():
    return os.environ.get('ABIS_URL', 'http://localhost:8030')

def index(request):
    req = requests.post(pr_url()+"/v1/persons?transactionId=portal", json=[{
        "attributeName":"firstName",
        "operator":"!=",
        "value":""
    }])
    if req.status_code!=200:
        raise Exception("Failed to contact Population Registry (HTTP code: %s)" % req.status_code)
    ret = []
    for x in req.json():
        pid = x['personId']
        req2 = requests.get(pr_url()+"/v1/persons/"+pid+"/reference?transactionId=portal")
        if req2.status_code!=200:
            logging.error("Failed to contact Population Registry (HTTP code: %s)" % req2.status_code)
        else:
            d = {'personId': pid}
            d.update(req2.json()['biographicData'])
            ret.append(d)
    return render(request, "pr/portal/index.html", dict(persons=ret))

def portrait(request, person_id):
    return render(request, "pr/portal/portrait.html", dict(personId=person_id))

def portrait_image(request, person_id):
    req = requests.get(abis_url()+"/v1/persons/"+person_id+'/encounters?transactionId=portal')
    if req.status_code!=200:
        raise Exception("Failed to contact ABIS (HTTP code: %s)" % req.status_code)
    data = req.json()
    if not data:
        raise Exception("No encounters found in ABIS for %s (HTTP code: %s)" % (person_id, req.status_code) )
    for bio in data[0]['biometricData']:
        if bio['biometricType'] == 'FACE':
            i = base64.b64decode(bio['image'])
            return HttpResponse(i, content_type='application/octet-stream')
    raise Exception("No portrait found in ABIS for %s (HTTP code: %s)" % (person_id, req.status_code) )

def person(request, person_id):
    req = requests.get(pr_url()+"/v1/persons/"+person_id+'/identities?transactionId=portal')
    if req.status_code!=200:
        raise Exception("Failed to contact Population Registry (HTTP code: %s)" % req.status_code)
    data = req.json()
    for i in data:
        i['biographicData']['dateOfBirth'] = datetime.date.fromisoformat(i['biographicData']['dateOfBirth'])
    #logging.error(data)
    return render(request, "pr/portal/person.html", dict(personId=person_id, identities=data))

def names(fn):
    ret = []
    with open(os.path.join(os.path.dirname(__file__),fn), 'rt') as f:
        for l in f.readlines():
            l = l.strip()
            if l and l[0]!='#':
                ret.append(l)
    return ret

def add_dummy(request):
    # Create some persons
    datap = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    gender = random.choice(['M', 'F'])
    dob = '%04d-%02d-%02d' % (random.randrange(1970, 2002), random.randrange(1, 12), random.randrange(1, 28))
    if gender=='M':
        fn = 'male.txt'
    else:
        fn = 'female.txt'
    datai = {
        "identityType": "CIVIL",
        "status": "VALID",
        "galleries": ["1"],
        "contextualData": {
            "enrollmentDate": datetime.date.today().isoformat(),
        },
        "biographicData": {
            "firstName": random.choice(names(fn)),
            "lastName": random.choice(names('surname.txt')),
            "dateOfBirth": dob,
            "gender": gender,
        }
    }

    # get a new UIN
    with requests.post(uin_url()+'/v1/uin', json=datai['biographicData'], params={'transactionId': 'portal'},verify=False) as req:
        if req.status_code!=200:
            raise Exception("Failed to contact UIN Generator (HTTP code: %s)" % req.status_code)
        UIN = req.json()

    # Create person
    with requests.post(pr_url()+'/v1/persons/'+UIN, json=datap, params={'transactionId': 'portal'},verify=False) as req:
        if req.status_code!=201:
            raise Exception("Failed to contact Population Registry (HTTP code: %s)" % req.status_code)

    # Create identity
    with requests.post(pr_url()+'/v1/persons/'+UIN+'/identities/001', json=datai, params={'transactionId': 'portal'},verify=False) as req:
        if req.status_code!=201:
            raise Exception("Failed to contact Population Registry (HTTP code: %s)" % req.status_code)
    with requests.put(pr_url()+'/v1/persons/'+UIN+'/identities/001/reference', params={'transactionId': 'portal'},verify=False) as req:
        if req.status_code!=204:
            raise Exception("Failed to contact Population Registry (HTTP code: %s)" % req.status_code)

    return HttpResponseRedirect(reverse("pr:index"))


@register.filter(is_safe=True)
def in_env(value):
    if value in os.environ:
        return '1'
    return '0'

