
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

import requests

from portal.views import enr_url

def index(request):
    ctx = dict(
        is_healthy=False,
        count=0,
    )

    try:
        req = requests.get(enr_url()+"monitoring/v1/is_healthy", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['is_healthy'] = True
        req = requests.get(enr_url()+"monitoring/v1/metrics/gauges/nb_enrollments/count", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['count'] = req.json()
    except:
        pass

    return render(request, "portal/osia/index.html", ctx)

