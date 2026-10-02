import ssl
import logging
import json

import yaml

import jsonschema
import referencing
import referencing.jsonschema

import aiohttp
from aiohttp import web



import cms


import livemetrics
import livemetrics.publishers.aiohttp



# [---CUSTO---]
# Additional imports
import io
import pprint
# [---CUSTO---]

routes = web.RouteTableDef()

if 'is_healthy' not in globals():
    def is_healthy():
        return True

if 'is_ready' not in globals():
    def is_ready():
        return True

LM = livemetrics.LiveMetrics(json.dumps(dict(version=cms.__version__)), "cms", is_healthy, is_ready)

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
    except aiohttp.web_exceptions.HTTPException:
        raise
    except Exception as exc:
        logging.exception("Exception caught in middleware: [%s]", str(exc))
        return web.json_response(dict(code=0, message=str(exc)), status=500)


# _____________________________________________________________________________
def get_ssl_context():
    ctx = None
    if cms.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", cms.args.server_certfile, cms.args.server_keyfile)
        if cms.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", cms.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=cms.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(cms.args.server_certfile,
                            cms.args.server_keyfile,
                            password=cms.args.server_keyfile_password)
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
    if cms.args.loglevel=='DEBUG':
        runner = web.AppRunner(app2)
    else:
        runner = web.AppRunner(app2, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=cms.args.ip, port=cms.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=cms.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    if 'on_startup' in globals():
        app.on_startup.append(on_startup)
    if 'on_shutdown' in globals():
        app.on_shutdown.append(on_shutdown)
    app.add_routes(routes)
    if cms.args.monitoring_port<=0 or cms.args.monitoring_port==cms.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if cms.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=cms.args.ip, port=cms.args.port, access_log=None, ssl_context=get_ssl_context())


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
        if cms.args and cms.args.api_file:
            with open(cms.args.api_file, 'r') as f:
                api = yaml.load(f, Loader=yaml.SafeLoader)
            schemas = api['components']['schemas']

            # [---CUSTO---]
            # Load the custo
            if cms.args and cms.args.custo_filename:
                with io.open(cms.args.custo_filename, 'rt', encoding='utf-8') as stream:
                    custo = yaml.load(stream, Loader=yaml.Loader)
                    # apply custo definition
                    for k,v in custo.items():
                        schemas[k] = v
                    logging.info("Custo from file [%s] was loaded", cms.args.custo_filename)
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




# [---CUSTO---]

# _____________________________________________________________________________
@routes.post('/v1/credentialRequests/{credentialRequestId}')
@LM.timer("createCredentialRequest", ok_status, "error")
async def createCredentialRequest(request):   # NOSONAR
    credential_request_id = request.match_info['credentialRequestId']
    transaction_id = request.query['transactionId']

    data = await request.json()
    logging.info("[%s] - Received CredentialRequest for id %s", transaction_id, credential_request_id)
    msg = validate_json(data, 'CredentialRequest')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)
    logging.info("[%s] - Data is correct", transaction_id)

    for bio in data['biometricData']:
        bio['image'] = '***'
    logging.debug("Processing request:\n%s\n", pprint.pformat(data,indent=2,sort_dicts=False))

    # No processing - this is a just a mock
    logging.info("[%s] - Processing finished", transaction_id)
    return web.Response(status=201)

# [---CUSTO---]
