import ssl
import logging
import json
import asyncio

import aiohttp
from aiohttp import web

import orchestrator
import orchestrator.tasks

import livemetrics
import livemetrics.publishers.aiohttp

routes = web.RouteTableDef()

def is_healthy():
    return True

LM = livemetrics.LiveMetrics(json.dumps(dict(version=orchestrator.__version__)), "orchestrator", is_healthy)

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
    except aiohttp.web_exceptions.HTTPException:
        raise
    except Exception as exc:
        logging.exception("Exception caught in middleware: [%s]", str(exc))
        return web.json_response(dict(code=0, message=str(exc)), status=500)


# _____________________________________________________________________________
def get_ssl_context():
    ctx = None
    if orchestrator.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", orchestrator.args.server_certfile, orchestrator.args.server_keyfile)
        if orchestrator.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", orchestrator.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=orchestrator.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(orchestrator.args.server_certfile,
                            orchestrator.args.server_keyfile,
                            password=orchestrator.args.server_keyfile_password)
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
    runner = web.AppRunner(app2)
    await runner.setup()
    site = web.TCPSite(runner, host=orchestrator.args.ip, port=orchestrator.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=orchestrator.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    app.add_routes(routes)
    if orchestrator.args.monitoring_port<=0 or orchestrator.args.monitoring_port==orchestrator.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)
    app.on_startup.append(register_topic)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if orchestrator.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=orchestrator.args.ip, port=orchestrator.args.port, access_log=None, ssl_context=get_ssl_context())


# _____________________________________________________________________________
async def register_topic(app):
    await asyncio.sleep(5)
    logging.info("Register for events from topic [CR]")
    params = {'topic':'CR', 'address': orchestrator.args.my_url+'cr_event', 'policy': '3,10'}

    try:
        async with aiohttp.ClientSession() as clt_session:
            async with clt_session.post(orchestrator.args.notification_url+"v1/topics", params={'name':'CR'}, ssl=False) as response:
                if response.status == 200:
                    await response.read()
                else:
                    logging.error("Failed to create topic [CR]")
            async with clt_session.post(orchestrator.args.notification_url+"v1/subscriptions", params=params, ssl=False) as response:
                if response.status == 200:
                    await response.read()
                else:
                    logging.error("Failed to subscribe on topic [CR]")
    except:
        logging.exception("Could not subscribe on topic CR")

# _____________________________________________________________________________
@routes.post('/cr_event')
@LM.timer("cr_event", ok_status, "error")
async def cr_event(request):
    logging.debug('Receiving notification')
    m = await request.json()

    if m['type']=='SubscriptionConfirmation':
        logging.info("Confirming subscription")
        logging.debug('Headers: '+str(request.headers))
        logging.debug(str(m))
        async with aiohttp.ClientSession() as clt_session:
            async with clt_session.get(m['confirmURL'], params={'token': m['token']}, ssl=False) as response:
                if response.status == 200:
                    await response.read()
                else:
                    logging.error("Failed to confirm subscription %s", m['confirmURL'])
                    return web.Response(status=400, body='')
    else:
        logging.debug("Notification")
        logging.debug('Headers: '+str(request.headers))
        logging.debug(str(m))
        if m['subject']=='liveBirth':
            event = json.loads(m['message'])
            logging.info("Live birth notification received from [%s] for uin [%s]", event['source'], event['uin'])
            t = orchestrator.tasks.workflow(event['uin'], 'liveBirth')
        else:
            logging.info("Ignoring event [%s]", m['subject'])
    return web.Response(status=200, body='')

