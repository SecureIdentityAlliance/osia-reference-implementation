
""""
The Celery tasks executed as part of the workflow
"""

import json
import os
import asyncio
import logging
import io
import datetime

from orchestrator.celery import app
from orchestrator.clients import enrollment, pr, cr, abis, cms

from celery import chain

#______________________________________________________________________________
@app.task(bind=True)
def readPersonAttributes_CR(self,ctx, url, enrollment_id, transaction_id):
    logging.info("==> [%s] reading data from CR for UIN %s", transaction_id, ctx['UIN'])
    res = None
    try:
        # Build person data
        res = asyncio.run( cr.readPersonAttributes(url+'/v1/persons', transaction_id, ctx['UIN']) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not read person attributes", transaction_id)
        raise Exception("Could not read person attributes")
    ctx['biographicData'] = res
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def readEnrollment_ENR(self,ctx, url, enrollment_id, transaction_id):
    logging.info("==> [%s] reading enrollment from Enrollment Server for enrollmentId %s", transaction_id, enrollment_id)
    res = None
    try:
        # Get data
        res = asyncio.run( enrollment.readEnrollment(url+'/v1/enrollments', transaction_id, enrollment_id) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not read enrollment", transaction_id)
        raise Exception("Could not read enrollment")
    ctx['biometricData'] = res['biometricData']
    ctx['contextualData'] = res['contextualData']
    ctx['enrollmentType'] = res['enrollmentType']
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def deleteEnrollment_ENR(self,ctx, url, enrollment_id, transaction_id):
    logging.info("==> [%s] deleting enrollment from Enrollment Server for enrollmentId %s", transaction_id, enrollment_id)
    res = None
    try:
        # Get data
        res = asyncio.run( enrollment.deleteEnrollment(url+'/v1/enrollments', transaction_id, enrollment_id) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not delete enrollment", transaction_id)
        raise Exception("Could not delete enrollment")
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def createPerson_PR(self,ctx, url,enrollment_id, transaction_id):
    logging.info("==> [%s] Creating person in PR for enrollment %s", transaction_id, enrollment_id)
    res = None
    try:
        # Build person data
        person = {}
        person['status'] = 'ACTIVE'
        person['physicalStatus'] = 'ALIVE'
        data = io.BytesIO(json.dumps(person).encode('latin-1'))
        res = asyncio.run( pr.createPerson(url+'/v1/persons', transaction_id, ctx['UIN'], data) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not create person", transaction_id)
        raise Exception("Could not create person")
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def createIdentity_PR(self,ctx, url,enrollment_id, transaction_id):
    logging.info("==> [%s] Creating identity in PR for enrollment %s", transaction_id, enrollment_id)
    try:
        # Get enrollment data (no biometrics)
        identity = dict(
            status='VALID',
            identityType=ctx.get('enrollmentType', 'CIVIL'),
            galleries=['ALL'],
            contextualData=ctx.get('contextualData', dict()),
            biographicData=ctx['biographicData'],
            biometricData=[],
            documentData=[]
        )

        data = io.BytesIO(json.dumps(identity).encode('latin-1'))
        identity_id = ctx.get('identityId', None)
        if identity_id is None:
            identity_id = asyncio.run( pr.createIdentity(url+'/v1/persons', transaction_id, ctx['UIN'], data) )
        else:
            if not asyncio.run( pr.createIdentityWithId(url+'/v1/persons', transaction_id, ctx['UIN'], identity_id, data) ):
                identity_id = None
    except Exception as exc:
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not identity_id:
        logging.error("[%s] Could not create identity", transaction_id)
        raise Exception("Could not create identity")
    ctx['identityId'] = identity_id
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def defineReference_PR(self,ctx, url,enrollment_id, transaction_id):
    logging.info("==> [%s] define reference identity in PR for enrollment %s", transaction_id, enrollment_id)
    try:
        asyncio.run( pr.defineReference(url+'/v1/persons', transaction_id, ctx['UIN'], ctx['identityId']) )
    except Exception as exc:
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def createEncounter_ABIS(self,ctx, url,enrollment_id, transaction_id):
    if not ctx.get('biometricData', []):
        logging.info("==> [%s] No biometric data for enrollment %s", transaction_id, enrollment_id)
        return
    logging.info("==> [%s] Creating encounter in ABIS for enrollment %s", transaction_id, enrollment_id)
    try:
        encounter = dict(
            status='ACTIVE',
            encounterType=ctx.get('enrollmentType', 'CIVIL'),
            galleries=['ALL'],
            contextualData=ctx.get('contextualData', dict()),
            biographicData={},
            biometricData=ctx.get('biometricData', []),
        )

        data = io.BytesIO(json.dumps(encounter).encode('latin-1'))
        encounter_id = ctx.get('identityId', None)
        asyncio.run( abis.createEncounter(url+'/v1/persons', transaction_id, ctx['UIN'], encounter_id, data) )
    except Exception as exc:
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def createCredentialRequest_CMS(self,ctx, url,enrollment_id, transaction_id):
    logging.info("==> [%s] Creating CredentialRequest in CMS for enrollment %s", transaction_id, enrollment_id)
    try:
        request = dict(
            status='PENDING',
            requestData={
                "priority": 1,
                "credentialProfileId": "ID_CARD",
                "requestType": "FIRST_ISSUANCE",
                "validFromDate": datetime.datetime.now().isoformat(),
                "validToDate": (datetime.datetime.now() + datetime.timedelta(days=4*365+1)).isoformat(),
                "issuingAuthority": "OSIA",
            },
            personId=ctx['UIN'],
            biographicData=ctx.get('biographicData', {}),
            biometricData=ctx.get('biometricData', [])
        )

        data = io.BytesIO(json.dumps(request).encode('latin-1'))
        asyncio.run( cms.createCredentialRequest(url, transaction_id, enrollment_id, data) )
    except Exception as exc:
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    return ctx

#______________________________________________________________________________
@app.task
def done(ctx, transaction_id):
    logging.info("==> [%s] - Workflow completed", transaction_id)

#______________________________________________________________________________
def workflow(uin, transaction_id, enrollment_id):
    logging.info('[%s] - Starting workflow for UIN [%s]', transaction_id, uin)
    ctx = {}
    ctx['UIN'] = uin
    ctx['identityId'] = datetime.datetime.now().strftime("%m%d%H%M%S%f")
    # See https://docs.celeryproject.org/en/stable/userguide/canvas.html#the-primitives
    chain( 
        readPersonAttributes_CR.s(ctx, os.environ.get("CR_URL",'http://cr:8080'), enrollment_id, transaction_id),
        createPerson_PR.s(os.environ.get("PR_URL",'http://pr:8080'), enrollment_id, transaction_id),
        createIdentity_PR.s(os.environ.get("PR_URL",'http://pr:8080'), enrollment_id, transaction_id),
        defineReference_PR.s(os.environ.get("PR_URL",'http://pr:8080'), enrollment_id, transaction_id),
        done.s(transaction_id),
    )()

#______________________________________________________________________________
def workflow_enroll4birth(uin, transaction_id, enrollment_id):
    logging.info('[%s] - Starting workflow "enroll4birth" for UIN [%s]', transaction_id, uin)
    ctx = {}
    ctx['UIN'] = uin
    ctx['identityId'] = datetime.datetime.now().strftime("%m%d%H%M%S%f")
    # See https://docs.celeryproject.org/en/stable/userguide/canvas.html#the-primitives
    chain( 
        # (12)
        readPersonAttributes_CR.s(ctx, os.environ.get("CR_URL",'http://cr:8080'), enrollment_id, transaction_id),
        # (13)
        readEnrollment_ENR.s(os.environ.get("ENROLLMENT_URL",'http://enrollment:8080'), enrollment_id, transaction_id),
        # (14)
        createPerson_PR.s(os.environ.get("PR_URL",'http://pr:8080'), enrollment_id, transaction_id),
        # (15)
        createIdentity_PR.s(os.environ.get("PR_URL",'http://pr:8080'), enrollment_id, transaction_id),
        # (16)
        defineReference_PR.s(os.environ.get("PR_URL",'http://pr:8080'), enrollment_id, transaction_id),
        # (17)
        createEncounter_ABIS.s(os.environ.get("ABIS_URL",'http://abis:8080'), enrollment_id, transaction_id),
        # (18) Send to CMS
        createCredentialRequest_CMS.s(os.environ.get("CMS_URL",'http://cms:8080'), enrollment_id, transaction_id),
        # (19) delete enrollment
        deleteEnrollment_ENR.s(os.environ.get("ENROLLMENT_URL",'http://enrollment:8080'), enrollment_id, transaction_id),
        done.s(transaction_id),
    )()

