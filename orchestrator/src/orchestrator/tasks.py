
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
from orchestrator.clients import pr, cr

from celery import chain

#______________________________________________________________________________
@app.task(bind=True)
def readPersonAttributes_CR(self,ctx, url, enrollment_id, transaction_id):
    logging.info("==> [%s] reading data from CR for UIN %s", transaction_id, ctx['UIN'])
    res = None
    try:
        # Build person data
        res = asyncio.run( cr.readPersonAttributes(url, transaction_id, ctx['UIN']) )
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
def createPerson_PR(self,ctx, url,enrollment_id, transaction_id):
    logging.info("==> [%s] Creating person in PR for enrollment %s", transaction_id, enrollment_id)
    res = None
    try:
        # Build person data
        person = {}
        person['status'] = 'ACTIVE'
        person['physicalStatus'] = 'ALIVE'
        data = io.BytesIO(json.dumps(person).encode('latin-1'))
        res = asyncio.run( pr.createPerson(url, transaction_id, ctx['UIN'], data) )
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
            identityType='CIVIL',
            galleries=['ALL'],
            contextualData=dict(
            ),
            biographicData=ctx['biographicData'],
            biometricData=[],
            documentData=[]
        )

        data = io.BytesIO(json.dumps(identity).encode('latin-1'))
        identity_id = ctx.get('identityId', None)
        if identity_id is None:
            identity_id = asyncio.run( pr.createIdentity(url, transaction_id, ctx['UIN'], data) )
        else:
            if not asyncio.run( pr.createIdentityWithId(url, transaction_id, ctx['UIN'], identity_id, data) ):
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
        asyncio.run( pr.defineReference(url, transaction_id, ctx['UIN'], ctx['identityId']) )
    except Exception as exc:
        self.retry(countdown=60.0,max_retries=10,exc=exc)
    return ctx

#______________________________________________________________________________
@app.task
def done(ctx, transaction_id):
    logging.info("==> [%s] - Workflow completed", transaction_id)

#______________________________________________________________________________
def workflow(uin, transaction_id):
    logging.info('[%s] - Starting workflow for UIN [%s]', transaction_id, uin)
    ctx = {}
    ctx['UIN'] = uin
    enrollment_id = '1'
    ctx['identityId'] = datetime.datetime.now().strftime("%m%d%H%M%S%f")
    # See https://docs.celeryproject.org/en/stable/userguide/canvas.html#the-primitives
    chain( 
        readPersonAttributes_CR.s(ctx, os.environ.get("CR_URL",'http://cr:8080/v1/persons'), enrollment_id, transaction_id),
        createPerson_PR.s(os.environ.get("PR_URL",'http://pr:8080/v1/persons'), enrollment_id, transaction_id),
        createIdentity_PR.s(os.environ.get("PR_URL",'http://pr:8080/v1/persons'), enrollment_id, transaction_id),
        defineReference_PR.s(os.environ.get("PR_URL",'http://pr:8080/v1/persons'), enrollment_id, transaction_id),
        done.s(transaction_id),
    )()

