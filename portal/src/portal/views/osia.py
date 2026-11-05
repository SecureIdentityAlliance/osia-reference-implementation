
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

import requests
import logging

from portal.views import enr_url, uin_url, notif_url, orch_url

def index(request):
    ctx = dict(
        enrollment=dict(
            is_healthy=False,
            count=0,
        ),
        uin=dict(
            is_healthy=False,
            count=0,
        ),
        notification=dict(
            is_healthy=False,
            count=0,
        ),
        orchestrator=dict(
            is_healthy=False,
            stats={},
        ),
    )

    # Get enrollment server stats
    try:
        req = requests.get(enr_url()+"monitoring/v1/is_healthy", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['enrollment']['is_healthy'] = True
        req = requests.get(enr_url()+"monitoring/v1/metrics/gauges/nb_enrollments/count", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['enrollment']['count'] = req.json()
    except:
        pass

    # Get UIN stats
    try:
        req = requests.get(uin_url()+"monitoring/v1/is_healthy", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['uin']['is_healthy'] = True
        req = requests.get(uin_url()+"monitoring/v1/metrics/meters/generateUIN/200/count", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['uin']['count'] = req.json()
    except:
        pass

    # Get Notification stats
    try:
        req = requests.get(notif_url()+"monitoring/v1/is_healthy", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['notification']['is_healthy'] = True
        req = requests.get(notif_url()+"monitoring/v1/metrics/meters/publish/200/count", verify=False, timeout=0.5)
        if req.status_code==200:
            ctx['notification']['count'] = req.json()
    except:
        pass

    # Get Orchestrator stats
    try:
        req = requests.get(orch_url()+"monitoring/v1/is_healthy", verify=False, timeout=1.5)
        if req.status_code==200:
            ctx['orchestrator']['is_healthy'] = True
        req = requests.get(orch_url()+"stats/total", verify=False, timeout=1.5)
        if req.status_code==200:
            ctx['orchestrator']['stats'] = req.json()
    except:
        pass

    return render(request, "portal/osia/index.html", ctx)

