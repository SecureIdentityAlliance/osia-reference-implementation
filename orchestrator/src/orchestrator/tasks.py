
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
from orchestrator.clients import enrollment, pr, cr, abis, cms, uin

from celery import chain

def get_url(name, default):
    u = os.environ.get(name, default)
    u = u+'/' if u and u[-1]!='/' else u
    return u

#______________________________________________________________________________
@app.task(bind=True)
def generate_UIN(self,ctx, url, enrollment_id, transaction_id):
    logging.info("==> [%s] generate UIN if not found in enrollment", transaction_id)
    if 'requestData' in ctx and 'UIN' in ctx['requestData']:
        ctx['UIN'] = ctx['requestData']['UIN']
        return ctx
    res = None
    try:
        # Generate new UIN
        res = asyncio.run( uin.generate(url+'v1/uin', transaction_id, ctx.get('biographicData', {})) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not generate new UIN", transaction_id)
        raise Exception("Could not generate new UIN")
    ctx['UIN'] = res
    return ctx


#______________________________________________________________________________
@app.task(bind=True)
def readPersonAttributes_CR(self,ctx, url, enrollment_id, transaction_id):
    logging.info("==> [%s] reading data from CR for UIN %s", transaction_id, ctx['UIN'])
    res = None
    try:
        # Build person data
        res = asyncio.run( cr.readPersonAttributes(url+'v1/persons', transaction_id, ctx['UIN']) )
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
        res = asyncio.run( enrollment.readEnrollment(url+'v1/enrollments', transaction_id, enrollment_id) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not read enrollment", transaction_id)
        raise Exception("Could not read enrollment")
    ctx['enrollmentType'] = res['enrollmentType']
    ctx['requestData'] = res['requestData']
    ctx['contextualData'] = res['contextualData']
    if 'biographicData' not in ctx:
        ctx['biographicData'] = res['biographicData']
        if 'parentUIN' in ctx['biographicData']:
            del ctx['biographicData']['parentUIN']
    ctx['biometricData'] = res['biometricData']
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def findEnrollment_ENR(self,ctx, url, enrollment_id, transaction_id):
    logging.info("==> [%s] finding enrollment from Enrollment Server for UIN [%s]", transaction_id, ctx['UIN'])
    res = None
    try:
        # Make the query
        res = asyncio.run( enrollment.findEnrollment_by_UIN(url+'v1/enrollments', transaction_id, ctx['UIN']) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.info("[%s] Could not find enrollment", transaction_id)
        return ctx
    ctx['enrollmentId'] = res[0]['enrollmentId']
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def deleteEnrollment_ENR(self,ctx, url, enrollment_id, transaction_id):
    if 'enrollmentId' in ctx:
        enrollment_id = ctx['enrollmentId']
    if not enrollment_id:
        return ctx
    logging.info("==> [%s] deleting enrollment from Enrollment Server for enrollmentId %s", transaction_id, enrollment_id)
    res = None
    try:
        # Get data
        res = asyncio.run( enrollment.deleteEnrollment(url+'v1/enrollments', transaction_id, enrollment_id) )
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
        res = asyncio.run( pr.createPerson(url+'v1/persons', transaction_id, ctx['UIN'], data) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not create person", transaction_id)
        raise Exception("Could not create person")
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def deletePerson_PR(self,ctx, url, enrollment_id, transaction_id):
    uin = ctx['UIN']
    logging.info("==> [%s] deleting person from Population Registry for UIN [%s]", transaction_id, uin)
    res = None
    try:
        res = asyncio.run( pr.deletePerson(url+'v1/persons', transaction_id, uin) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not delete person", transaction_id)
        raise Exception("Could not delete person")
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def createIdentity_PR(self,ctx, url,enrollment_id, transaction_id):
    logging.info("==> [%s] Creating identity in PR for enrollment %s", transaction_id, enrollment_id)
    try:
        # Get enrollment data (no biometrics)
        identity = dict(
            status='VALID',
            identityType=ctx.get('enrollmentType', 'CHILD'),
            galleries=['DEMO'],
            contextualData=ctx.get('contextualData', dict()),
            biographicData=ctx['biographicData'],
            biometricData=[],
            documentData=[]
        )
        # Insert only the portrait in PR (enroll4birth demo)
        identity['biometricData'] = list(filter(lambda x: x['biometricType']=='FACE', ctx.get('biometricData', [])))
        data = io.BytesIO(json.dumps(identity).encode('latin-1'))
        identity_id = ctx.get('identityId', None)
        if identity_id is None:
            identity_id = asyncio.run( pr.createIdentity(url+'v1/persons', transaction_id, ctx['UIN'], data) )
        else:
            if not asyncio.run( pr.createIdentityWithId(url+'v1/persons', transaction_id, ctx['UIN'], identity_id, data) ):
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
        asyncio.run( pr.defineReference(url+'v1/persons', transaction_id, ctx['UIN'], ctx['identityId']) )
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
            encounterType=ctx.get('enrollmentType', 'CHILD'),
            galleries=['DEMO'],
            contextualData=ctx.get('contextualData', dict()),
            biographicData={},
            biometricData=ctx.get('biometricData', []),
        )

        data = io.BytesIO(json.dumps(encounter).encode('latin-1'))
        encounter_id = ctx.get('identityId', None)
        asyncio.run( abis.createEncounter(url+'v1/persons', transaction_id, ctx['UIN'], encounter_id, data) )
    except Exception as exc:
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    return ctx

#______________________________________________________________________________
@app.task(bind=True)
def deleteAll_ABIS(self,ctx, url, enrollment_id, transaction_id):
    uin = ctx['UIN']
    logging.info("==> [%s] deleting all encounters from ABIS for UIN [%s]", transaction_id, uin)
    res = None
    try:
        res = asyncio.run( abis.deleteAll(url+'v1/persons', transaction_id, uin) )
    except Exception as exc:
        logging.exception("error")
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    if not res:
        logging.error("[%s] Could not delete person", transaction_id)
        raise Exception("Could not delete person")
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
        readPersonAttributes_CR.s(ctx, get_url("CR_URL",'http://cr:8080/'), enrollment_id, transaction_id),
        createPerson_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        createIdentity_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        defineReference_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        done.s(transaction_id),
    )()

#______________________________________________________________________________
def workflow_enroll4birth_parent(transaction_id, enrollment_id):
    logging.info('[%s] - Starting workflow "enroll4birth_parent"', transaction_id)
    ctx = {}
    ctx['UIN'] = None
    ctx['identityId'] = datetime.datetime.now().strftime("%m%d%H%M%S%f")
    # See https://docs.celeryproject.org/en/stable/userguide/canvas.html#the-primitives
    chain( 
        readEnrollment_ENR.s(ctx, get_url("ENROLLMENT_URL",'http://enrollment:8080/'), enrollment_id, transaction_id),
        generate_UIN.s(get_url("UIN_URL",'http://uin:8080/'), enrollment_id, transaction_id),
        createPerson_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        createIdentity_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        defineReference_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        createEncounter_ABIS.s(get_url("ABIS_URL",'http://abis:8080/'), enrollment_id, transaction_id),
        # deleteEnrollment_ENR.s(get_url("ENROLLMENT_URL",'http://enrollment:8080/'), enrollment_id, transaction_id),
        done.s(transaction_id),
    )()

#______________________________________________________________________________
def workflow_enroll4birth_delete(transaction_id, uin):
    logging.info('[%s] - Starting workflow "enroll4birth_delete" for UIN [%s]', transaction_id, uin)
    ctx = {}
    ctx['UIN'] = uin
    enrollment_id = None
    # See https://docs.celeryproject.org/en/stable/userguide/canvas.html#the-primitives
    chain(
        findEnrollment_ENR.s(ctx, get_url("ENROLLMENT_URL",'http://enrollment:8080/'), enrollment_id, transaction_id),
        deleteEnrollment_ENR.s(get_url("ENROLLMENT_URL",'http://enrollment:8080/'), enrollment_id, transaction_id),
        deletePerson_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        deleteAll_ABIS.s(get_url("ABIS_URL",'http://abis:8080/'), enrollment_id, transaction_id),
        done.s(transaction_id),
    )()

#______________________________________________________________________________
def workflow_enroll4birth_child(uin, transaction_id, enrollment_id):
    logging.info('[%s] - Starting workflow "enroll4birth" for UIN [%s]', transaction_id, uin)
    ctx = {}
    ctx['UIN'] = uin
    ctx['identityId'] = datetime.datetime.now().strftime("%m%d%H%M%S%f")
    # See https://docs.celeryproject.org/en/stable/userguide/canvas.html#the-primitives
    chain( 
        # (12)
        readPersonAttributes_CR.s(ctx, get_url("CR_URL",'http://cr:8080/'), enrollment_id, transaction_id),
        # (13)
        readEnrollment_ENR.s(get_url("ENROLLMENT_URL",'http://enrollment:8080/'), enrollment_id, transaction_id),
        # (14)
        createPerson_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        # (15)
        createIdentity_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        # (16)
        defineReference_PR.s(get_url("PR_URL",'http://pr:8080/'), enrollment_id, transaction_id),
        # (17)
        createEncounter_ABIS.s(get_url("ABIS_URL",'http://abis:8080/'), enrollment_id, transaction_id),
        # (18) Send to CMS
        createCredentialRequest_CMS.s(get_url("CMS_URL",'http://cms:8080/'), enrollment_id, transaction_id),
        # (19) delete enrollment
        # deleteEnrollment_ENR.s(get_url("ENROLLMENT_URL",'http://enrollment:8080/'), enrollment_id, transaction_id),
        done.s(transaction_id),
    )()

