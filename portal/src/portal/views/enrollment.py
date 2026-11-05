import logging
import os
import datetime
import random
import base64

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

import requests

from portal.views import enr_url

def index(request):
    req = requests.post(enr_url()+"v1/enrollments?transactionId=portal", json=[{
        "attributeName":"firstName",
        "operator":"!=",
        "value":""
    }])
    if req.status_code!=200:
        raise Exception("Failed to contact Enrollment Server (HTTP code: %s)" % req.status_code)
    ret = reversed(req.json())
    return render(request, "portal/enrollment/index.html", dict(enrollments=ret))

def portrait_image(request, enrollment_id):
    req = requests.get(enr_url()+"v1/enrollments/"+enrollment_id+'?transactionId=portal')
    if req.status_code!=200:
        raise Exception("Failed to contact Enrollment Server (HTTP code: %s)" % req.status_code)
    data = req.json()
    for bio in data['biometricData']:
        if bio['biometricType'] == 'FACE':
            i = base64.b64decode(bio['image'])
            return HttpResponse(i, content_type='application/octet-stream')
    raise Exception("No portrait found in Enrollment Server for %s (HTTP code: %s)" % (enrollment_id, req.status_code) )
