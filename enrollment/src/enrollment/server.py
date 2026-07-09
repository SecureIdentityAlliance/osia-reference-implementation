import ssl
import logging
import json

import yaml

import jsonschema
import referencing
import referencing.jsonschema

import aiohttp
from aiohttp import web

import asyncio

from sqlalchemy.orm import Session, make_transient
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


import enrollment
import enrollment.model

import livemetrics
import livemetrics.publishers.aiohttp


# An exception class to propagate web.Response
class ResponseException(BaseException):
    def __init__(self, response):
        self.response = response


# [---CUSTO---]
# Additional imports

import uuid
import hashlib

# [---CUSTO---]

routes = web.RouteTableDef()

if 'is_healthy' not in globals():
    def is_healthy():
        return True

if 'is_ready' not in globals():
    def is_ready():
        return True

LM = livemetrics.LiveMetrics(json.dumps(dict(version=enrollment.__version__)), "enrollment", is_healthy, is_ready)

def ok_status(ret):
    return str(ret.status)


# _____________________________________________________________________________
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status >= 400:
            logging.info("Request failed with HTTP error %d", response.status)
        return response
    # [---CUSTO---]
    # Manage additional exceptions
    except KeyError as exc:
        if exc.args==('transactionId',):
                return web.json_response({'code':1, 'message': 'Missing transactionId'}, status=400)
        raise
    # [---CUSTO---]
    # 
    except ResponseException as resp:
        return resp.response
    # 
    except aiohttp.web_exceptions.HTTPException:
        raise
    except Exception as exc:
        logging.exception("Exception caught in middleware: [%s]", str(exc))
        return web.json_response(dict(code=0, message=str(exc)), status=500)


# _____________________________________________________________________________
def get_ssl_context():
    ctx = None
    if enrollment.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", enrollment.args.server_certfile, enrollment.args.server_keyfile)
        if enrollment.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", enrollment.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=enrollment.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(enrollment.args.server_certfile,
                            enrollment.args.server_keyfile,
                            password=enrollment.args.server_keyfile_password)
        logging.debug("certfile/keyfile loaded for SSL Context")
    return ctx

  
#______________________________________________________________________________
def get_notification_client_ssl_context():
    ctx = False
    if enrollment.args.notification_ca_certfile:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=enrollment.args.notification_ca_certfile)
        logging.debug("notification SSL Context setup for CA FILE: %s", enrollment.args.notification_ca_certfile)

        if enrollment.args.notification_certfile:
            ctx.load_cert_chain(enrollment.args.notification_certfile,
                                keyfile=enrollment.args.notification_keyfile,
                                password=enrollment.args.notification_keyfile_password)
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
            logging.debug("certfile/keyfile loaded for SSL Context [%s, %s]", enrollment.args.notification_certfile, enrollment.args.notification_keyfile)
    return ctx


# _____________________________________________________________________________
async def _strip_server(req, res):
    if 'Server' in res.headers:
        del res.headers['Server']


# _____________________________________________________________________________
async def start_monitoring(app):
    app2 = web.Application(middlewares=[error_middleware])
    app2.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    if enrollment.args.loglevel=='DEBUG':
        runner = web.AppRunner(app2)
    else:
        runner = web.AppRunner(app2, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=enrollment.args.ip, port=enrollment.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=enrollment.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    if 'on_startup' in globals():
        app.on_startup.append(on_startup)
    if 'on_shutdown' in globals():
        app.on_shutdown.append(on_shutdown)
    app.add_routes(routes)
    if enrollment.args.monitoring_port<=0 or enrollment.args.monitoring_port==enrollment.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if enrollment.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=enrollment.args.ip, port=enrollment.args.port, access_log=None, ssl_context=get_ssl_context())

    logging.info('Closing application...')
    if enrollment.aengine:
        # proper cleanup of async engine
        asyncio.run(enrollment.aengine.dispose())
        logging.info('Async engine closed')


# _____________________________________________________________________________
def to_bool(x):
    if x in [True, 'True', 'true', 1, '1', 'yes', 'y', 'Y', 'Yes', 'YES']:
        return True
    return False

# Schema validation
registry = None
schemas = None
api = None
def validate_json(data, schema_name, with_required=True):
    global schemas
    global api
    global registry
    if not schemas or not api:
        if enrollment.args and enrollment.args.api_file:
            with open(enrollment.args.api_file, 'r') as f:
                api = yaml.load(f, Loader=yaml.SafeLoader)
            schemas = api['components']['schemas']

            # apply custo definition
            if enrollment.model.custo:
                for k,v in enrollment.model.custo.items():
                    schemas[k] = v
            # [---CUSTO---]
            # patch schemas for readOnly attributes
            schemas['Enrollment']['required'].remove('enrollmentId')

            # [---CUSTO---]

            registry = referencing.Registry().with_resource(
                uri='',
                resource=referencing.Resource.from_contents(api, default_specification=referencing.jsonschema.DRAFT7)
            )
            registry = registry.crawl()
        else:
            logging.debug('No validation of incoming JSON')
            return None
    # validate the data against the schema
    v = jsonschema.Draft7Validator(schema=schemas[schema_name], registry=registry, _resolver = registry.resolver())
    if with_required:
        msg = "\n".join([error.message for error in v.iter_errors(instance=data)])
    else:
        # do not check required field or None value
        msg = "\n".join([error.message for error in v.iter_errors(instance=data) if error.message.find('is a required property')<0 and error.message.find('None is not of type')<0])
    
    if msg:
        logging.error(msg)
        return msg


# _____________________________________________________________________________
def gauge_nb_enrollments():
    if not enrollment.engine:
        return 0
    with Session(enrollment.engine) as session, session.begin():
        return session.query(enrollment.model.Enrollment).count()
LM.gauge('nb_enrollments', gauge_nb_enrollments)

# _____________________________________________________________________________
def gauge_nb_biometricdata():
    if not enrollment.engine:
        return 0
    with Session(enrollment.engine) as session, session.begin():
        return session.query(enrollment.model.BiometricData).count()
LM.gauge('nb_biometricdata', gauge_nb_biometricdata)

# _____________________________________________________________________________
def gauge_nb_buffers():
    if not enrollment.engine:
        return 0
    with Session(enrollment.engine) as session, session.begin():
        return session.query(enrollment.model.Buffer).count()
LM.gauge('nb_buffers', gauge_nb_buffers)


# _____________________________________________________________________________
async def _aget_enrollment(session, enrollment_id):
    res = await enrollment.model.Enrollment.afind_by_id(session, enrollment_id)
    if len(res) > 1:
        raise ResponseException(web.Response(status=400))
    if len(res) < 1:
        raise ResponseException(web.Response(status=404))
    return res[0]


# [---CUSTO---]

#______________________________________________________________________________
async def finalize_CB(enrollment_id, transaction_id):
    """
    Function called when an enrollment is finalized.
    To be replaced with a real implementation
    """
    logging.info("Enrollment finalized")
    if not enrollment.args.notification_url:
        return
    async with aiohttp.ClientSession() as clt_session:
        try:
            async with clt_session.post(enrollment.args.notification_url+'/v1/topics/enrollment/publish', 
                                        json=dict(enrollmentId=enrollment_id, transactionId=transaction_id),
                                        ssl=get_notification_client_ssl_context()) as response:
                if response.status == 200:
                    await response.read()
                else:
                    buf = await response.read()
                    logging.error("Could not send the notification event [%s]", str(buf))
        except aiohttp.client_exceptions.ClientConnectorError:
            logging.error("Error reaching the notification service")

#______________________________________________________________________________
@routes.post('/v1/enrollments/{enrollment_id}')
async def createEnrollment(request):
    transaction_id = request.query['transactionId']
    finalize = json.loads(request.query.get('finalize','false'))
    enrollment_id = request.match_info['enrollment_id']
    data = await request.json()
    logging.info("[%s] - createEnrollment for enrollmentId [%s]", transaction_id, enrollment_id)

    msg = validate_json(data, 'Enrollment')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    logging.info('Receiving enrollment for transaction %s enrollmentId %s', transaction_id, enrollment_id)

    import enrollment.serialize
    async with AsyncSession(enrollment.aengine) as session, session.begin():
        # check that enrollment does not exist
        res = await enrollment.model.Enrollment.afind_by_id(session, enrollment_id)
        if res:
            logging.error("Enrollment already exists for id %s", enrollment_id)
            return web.Response(status=400)

        enrollment_schema = enrollment.serialize.EnrollmentSchema()
        np = enrollment_schema.load(data, session=session)
        np.enrollmentId = enrollment_id
        if finalize:
            np.status = 'FINALIZED'
        session.add(np)

        # Successful
        if np.status == 'FINALIZED':
            await finalize_CB(enrollment_id, transaction_id)
    return web.json_response(data=enrollment_id, status=201)

# _____________________________________________________________________________
@routes.post('/v1/enrollments')
@LM.timer("findEnrollments", ok_status, "error")
async def findEnrollments(request):
    transaction_id = request.query['transactionId']
    offset = int(request.query.get('offset', 0))
    limit = int(request.query.get('limit', 100))

    data = await request.json()
    logging.info("[%s] - findEnrollments", transaction_id)

    msg = validate_json(data, 'Expressions')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    # build predicate
    import enrollment.serialize
    async with AsyncSession(enrollment.aengine) as session, session.begin():
        sel = enrollment.model._build_predicate(data, limit, offset)
        if type(sel) is dict:
            logging.error(sel)
            return web.json_response(sel, status=400)
        res = await session.scalars(sel)

        enrollment_schema = enrollment.serialize.EnrollmentSchema()
        ret = []
        for o in res:
            ret.append( enrollment_schema.dump(o) )
        return web.json_response(ret, status=200)

#______________________________________________________________________________
@routes.get('/v1/enrollments/{enrollment_id}')
async def readEnrollment(request):
    transaction_id = request.query['transactionId']
    enrollment_id = request.match_info['enrollment_id']
    logging.info("[%s] - readEnrollment for enrollmentId [%s]", transaction_id, enrollment_id)

    import enrollment.serialize
    async with AsyncSession(enrollment.aengine) as session, session.begin():
        p = await _aget_enrollment(session, enrollment_id)
        enrollment_schema = enrollment.serialize.EnrollmentSchema()
        data = enrollment_schema.dump(p)
        return web.json_response(data, status=200)

#______________________________________________________________________________
@routes.put('/v1/enrollments/{enrollment_id}')
async def updateEnrollment(request):
    transaction_id = request.query['transactionId']
    finalize = json.loads(request.query.get('finalize','false'))
    enrollment_id = request.match_info['enrollment_id']

    logging.info("[%s] - updateEnrollment for enrollmentId [%s]", transaction_id, enrollment_id)

    import enrollment.serialize
    async with AsyncSession(enrollment.aengine) as session, session.begin():
        p = await _aget_enrollment(session, enrollment_id)
        if p.status == 'FINALIZED':
            logging.error('Enrollment %s already finalized', enrollment_id)
            return web.json_response(data={'code': 403, 'message': "Already finalized"}, status=403)

        data = await request.json()

        msg = validate_json(data, 'Enrollment')
        if msg:
            return web.json_response(data={'code': 400, 'message': msg}, status=400)

        # Make sure enrollmentId is set properly
        data['enrollmentId'] = enrollment_id
        if finalize:
            data['status'] = 'FINALIZED'

        await session.delete(p)
        await session.flush()
        enrollment_schema = enrollment.serialize.EnrollmentSchema()
        np = enrollment_schema.load(data, session=session)
        np.enrollmentId = enrollment_id
        session.add(np)

        # Successful
        if finalize:
            await finalize_CB(enrollment_id, transaction_id)
    return web.json_response(status=204)

#______________________________________________________________________________
@routes.patch('/v1/enrollments/{enrollment_id}')
async def partialUpdateEnrollment(request):
    transaction_id = request.query['transactionId']
    finalize = json.loads(request.query.get('finalize','false'))
    enrollment_id = request.match_info['enrollment_id']

    logging.info("[%s] - partialUpdateEnrollment for enrollmentId [%s]", transaction_id, enrollment_id)

    import enrollment.serialize
    async with AsyncSession(enrollment.aengine) as session, session.begin():
        p = await _aget_enrollment(session, enrollment_id)
        if p.status == 'FINALIZED':
            logging.error('Enrollment %s already finalized', enrollment_id)
            return web.json_response(data={'code': 403, 'message': "Already finalized"}, status=403)

        data = await request.json()

        msg = validate_json(data, 'Enrollment', with_required=False)
        if msg:
            return web.json_response(data={'code': 400, 'message': msg}, status=400)

        # Make sure enrollmentId is set properly
        data['enrollmentId'] = enrollment_id
        if finalize:
            data['status'] = 'FINALIZED'

        enrollment_schema = enrollment.serialize.EnrollmentSchema()
        enrollment_schema.load(data, instance=p, session=session, partial=True)
        p.enrollmentId = enrollment_id
        session.add(p)

        # Successful
        if finalize:
            await finalize_CB(enrollment_id, transaction_id)
    return web.json_response(status=204)

#______________________________________________________________________________
@routes.put('/v1/enrollments/{enrollment_id}/finalize')
async def finalizeEnrollment(request):
    transaction_id = request.query['transactionId']
    enrollment_id = request.match_info['enrollment_id']

    logging.info("[%s] - finalizeEnrollment for enrollmentId [%s]", transaction_id, enrollment_id)

    async with AsyncSession(enrollment.aengine) as session, session.begin():
        p = await _aget_enrollment(session, enrollment_id)
        if p.status == 'FINALIZED':
            logging.error('Enrollment %s already finalized', enrollment_id)
            return web.json_response(data={'code': 403, 'message': "Already finalized"}, status=403)

        p.status = 'FINALIZED'
        session.add(p)

    await finalize_CB(enrollment_id, transaction_id)

    return web.Response(status=204)

#______________________________________________________________________________
@routes.delete('/v1/enrollments/{enrollment_id}')
async def deleteEnrollment(request):
    transaction_id = request.query['transactionId']
    enrollment_id = request.match_info['enrollment_id']

    logging.info("[%s] - deleteEnrollment for enrollmentId [%s]", transaction_id, enrollment_id)

    async with AsyncSession(enrollment.aengine) as session, session.begin():
        p = await _aget_enrollment(session, enrollment_id)

        await session.delete(p)

        # delete attached buffer
        bufs = await enrollment.model.Buffer.afind_by_enrollment_id(session, enrollment_id)
        for buf in bufs:
            await session.delete(buf)

        return web.Response(status=204)

#______________________________________________________________________________
@routes.post('/v1/enrollments/{enrollment_id}/buffer')
async def createBuffer(request):
    transaction_id = request.query['transactionId']
    enrollment_id = request.match_info['enrollment_id']
    data = await request.read()
    ct = request.headers.get('content-type', '')
    digest = request.headers.get('Digest', None)

    logging.info("[%s] - createBuffer for enrollmentId [%s] (content-type: %s, Digest: %s, length: %s)", transaction_id, enrollment_id, ct, digest, len(data))

    # Check the digest
    if digest:
        if digest.startswith('SHA'):
            S = hashlib.sha1()
            S.update(data)
            ndigest = 'SHA='+S.hexdigest()
        else:
            S = hashlib.md5()
            S.update(data)
            ndigest = 'MD5='+S.hexdigest()
        if digest != ndigest:
            return web.Response(body='Incorrect digest', status=400)

    # Save in database
    async with AsyncSession(enrollment.aengine) as session, session.begin():
        buffer_id = str(uuid.uuid4())

        buf = enrollment.model.Buffer(id=buffer_id,
                                    enrollment_id = enrollment_id,
                                    buffer = data,
                                    content_type = ct)
        session.add(buf)

        # Successful
        return web.json_response(data=dict(bufferId=buffer_id), status=201)

#______________________________________________________________________________
@routes.get('/v1/enrollments/{enrollment_id}/buffer/{buffer_id}')
async def readBuffer(request):
    transaction_id = request.query['transactionId']
    enrollment_id = request.match_info['enrollment_id']
    buffer_id = request.match_info['buffer_id']

    logging.info("[%s] - readBuffer for enrollmentId/bufferId [%s]/[%s]", transaction_id, enrollment_id, buffer_id)

    async with AsyncSession(enrollment.aengine) as session, session.begin():

        bufs = await enrollment.model.Buffer.afind_by_id(session, enrollment_id, buffer_id)

        if len(bufs) > 1:
            return web.Response(status=400)
        if len(bufs) < 1:
            return web.Response(status=404)
        buf = bufs[0]
        data, content_type = buf.buffer, buf.content_type

        S = hashlib.sha1()
        S.update(data)
        digest = 'SHA='+S.hexdigest()
        return web.Response(body=data, status=200, headers={'content-type': content_type, 'Digest': digest} if content_type else {'Digest': digest})

# [---CUSTO---]
