import logging
import os
import datetime
import random

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

import requests

def pr_url():
    return os.environ.get('PR_URL', 'http://localhost:8010')

def uin_url():
    return os.environ.get('UIN_URL', 'http://localhost:8020')

def index(request):
    req = requests.get(pr_url()+"/v1/persons?names=firstName&names=lastName&names=personId")
    if req.status_code!=200:
        raise Exception("Failed to contact Population Registry (HTTP code: %s)" % req.status_code)
    return render(request, "pr/portal/index.html", dict(persons=req.json()))

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
        "contextualData": {
            "enrollmentDate": datetime.date.today().isoformat(),
        },
        "biographicData": {
            "firstName": random.choice(names(fn)),
            "lastName": random.choice(names('surname.txt')),
            "dateOfBirth": dob,
            "gender": gender,
            "nationality": "ENG",
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
    with requests.post(pr_url()+'/v1/persons/'+UIN+'/identities', json=datai, params={'transactionId': 'portal'},verify=False) as req:
        if req.status_code!=200:
            raise Exception("Failed to contact Population Registry (HTTP code: %s)" % req.status_code)

    return HttpResponseRedirect(reverse("pr:index"))
