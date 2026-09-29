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


import abis
import abis.model

import livemetrics
import livemetrics.publishers.aiohttp


# An exception class to propagate web.Response
class ResponseException(BaseException):
    def __init__(self, response):
        self.response = response


# [---CUSTO---]
# Additional imports
# [---CUSTO---]

routes = web.RouteTableDef()

if 'is_healthy' not in globals():
    def is_healthy():
        return True

if 'is_ready' not in globals():
    def is_ready():
        return True

LM = livemetrics.LiveMetrics(json.dumps(dict(version=abis.__version__)), "abis", is_healthy, is_ready)

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
    if abis.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", abis.args.server_certfile, abis.args.server_keyfile)
        if abis.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", abis.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=abis.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(abis.args.server_certfile,
                            abis.args.server_keyfile,
                            password=abis.args.server_keyfile_password)
        logging.debug("certfile/keyfile loaded for SSL Context")
    return ctx

  

# _____________________________________________________________________________
async def _strip_server(req, res):
    if 'Server' in res.headers:
        del res.headers['Server']


# _____________________________________________________________________________
async def start_monitoring(app):
    app2 = web.Application(middlewares=[error_middleware])
    app2.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    if abis.args.loglevel=='DEBUG':
        runner = web.AppRunner(app2)
    else:
        runner = web.AppRunner(app2, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=abis.args.ip, port=abis.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=abis.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    if 'on_startup' in globals():
        app.on_startup.append(on_startup)
    if 'on_shutdown' in globals():
        app.on_shutdown.append(on_shutdown)
    app.add_routes(routes)
    if abis.args.monitoring_port<=0 or abis.args.monitoring_port==abis.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if abis.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=abis.args.ip, port=abis.args.port, access_log=None, ssl_context=get_ssl_context())

    logging.info('Closing application...')
    if abis.aengine:
        # proper cleanup of async engine
        asyncio.run(abis.aengine.dispose())
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
        if abis.args and abis.args.api_file:
            with open(abis.args.api_file, 'r') as f:
                api = yaml.load(f, Loader=yaml.SafeLoader)
            schemas = api['components']['schemas']

            # apply custo definition
            if abis.model.custo:
                for k,v in abis.model.custo.items():
                    schemas[k] = v
            # [---CUSTO---]
            # patch schemas for readOnly attributes
            schemas['Encounter']['required'].remove('encounterId')
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
def gauge_nb_encounters():
    if not abis.engine:
        return 0
    with Session(abis.engine) as session, session.begin():
        return session.query(abis.model.Encounter).count()
LM.gauge('nb_encounters', gauge_nb_encounters)

# _____________________________________________________________________________
def gauge_nb_biometricdata():
    if not abis.engine:
        return 0
    with Session(abis.engine) as session, session.begin():
        return session.query(abis.model.BiometricData).count()
LM.gauge('nb_biometricdata', gauge_nb_biometricdata)



# [---CUSTO---]

# _____________________________________________________________________________
@routes.post('/v1/persons/{personId}/encounters/{encounterId}')
@LM.timer("createEncounter", ok_status, "error")
async def createEncounter(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    encounter_id = request.match_info['encounterId']

    data = await request.json()
    logging.info("[%s] - createEncounter for personId [%s]/[%s]", transaction_id, person_id, encounter_id)

    msg = validate_json(data, 'Encounter')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    import abis.serialize

    async with AsyncSession(abis.aengine) as session, session.begin():
        e = await abis.model.Encounter.afind_by_id(session, person_id, encounter_id)
        if e:
            return web.json_response(data={'code': 1, 'message': f'encounterId [{encounter_id}] already present in person [{person_id}]'}, status=409)

        encounter_schema = abis.serialize.EncounterSchema()
        ne = encounter_schema.load(data, session=session)
        ne.personId = person_id
        ne.encounterId = encounter_id
        session.add(ne)

        return web.json_response(data={'personId': person_id, 'encounterId': encounter_id}, status=200)

@routes.post('/v1/verify/{galleryId}/{personId}')
@LM.timer("verifyFromId", ok_status, "error")
async def verifyFromId(request):
    transaction_id = request.query['transactionId']
    gallery_id = request.match_info['galleryId']
    person_id = request.match_info['personId']

    data = await request.json()
    logging.info("[%s] - verifyFromId for personId [%s]/[%s]", transaction_id, gallery_id, person_id)

    # Use Encounter structure to validate the array of BiometricData
    if 'status' not in data:
        data['status'] = 'ACTIVE'
    if 'encounterType' not in data:
        data['encounterType'] = 'TYPE'
    msg = validate_json(data, 'Encounter')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    async with AsyncSession(abis.aengine) as session, session.begin():
        e = await abis.model.Encounter.afind_by_pid(session, person_id)
        if e:
            # it's a HIT !
            ret = {
                "decision": True,
                "scores": [
                    {
                        "score": 3500,
                        "encounterId": e[0].encounterId,
                    }]
                }
        else:
            ret = {
                "decision": False
                }
        return web.json_response(data=ret, status=200)

# [---CUSTO---]
