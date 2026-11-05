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

# is_healthy using control.ping: https://docs.celeryq.dev/en/stable/reference/celery.app.control.html#celery.app.control.Control.ping
def is_healthy():
    # ping: {'celery@ca172565cf52': {'ok': 'pong'}}
    for k, v in orchestrator.tasks.app.control.inspect().ping().items():
        if 'ok' not in v:
            return False
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

    try:
        async with aiohttp.ClientSession() as clt_session:
            logging.info("Register for events from topic [CR]")
            params = {'topic':'CR', 'address': orchestrator.args.my_url+'cr_event', 'policy': '3,10'}
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

            logging.info("Register for events from topic [enrollment]")
            params = {'topic':'enrollment', 'address': orchestrator.args.my_url+'enrollment_event', 'policy': '3,10'}
            async with clt_session.post(orchestrator.args.notification_url+"v1/topics", params={'name':'enrollment'}, ssl=False) as response:
                if response.status == 200:
                    await response.read()
                else:
                    logging.error("Failed to create topic [enrollment]")
            async with clt_session.post(orchestrator.args.notification_url+"v1/subscriptions", params=params, ssl=False) as response:
                if response.status == 200:
                    await response.read()
                else:
                    logging.error("Failed to subscribe on topic [enrollment]")
    except:
        logging.exception("Could not subscribe on topics CR and/or enrollment")


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
            transaction_id = event.get('transactionId', 'liveBirth')
            if 'enrollmentId' in event:
                t = orchestrator.tasks.workflow_enroll4birth_child(event['uin'], transaction_id, event['enrollmentId'])
            else:
                t = orchestrator.tasks.workflow(event['uin'], transaction_id, '1')
        else:
            logging.info("Ignoring event [%s]", m['subject'])
    return web.Response(status=200, body='')

# _____________________________________________________________________________
@routes.post('/enrollment_event')
@LM.timer("enrollment_event", ok_status, "error")
async def enrollment_event(request):
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

        if m['subject']=='parentEnrollment':
            event = json.loads(m['message'])
            logging.info("Parent enrollment notification received from [%s]", event['source'])
            transaction_id = event.get('transactionId', 'parentEnrollment')
            t = orchestrator.tasks.workflow_enroll4birth_parent(transaction_id, event['enrollmentId'])
        elif m['subject']=='deleteEnrollment':
            event = json.loads(m['message'])
            logging.info("Delete enrollment notification received from [%s]", event['source'])
            transaction_id = event.get('transactionId', 'deleteEnrollment')
            t = orchestrator.tasks.workflow_enroll4birth_delete(transaction_id, event['uin'])
        else:
            logging.info("Ignoring event [%s]", m['subject'])
    return web.Response(status=200, body='')

# _____________________________________________________________________________
@routes.get('/stats/total')
async def stats(request):
    logging.debug('stats/total')
    # See https://docs.celeryq.dev/en/stable/reference/celery.app.control.html#celery.app.control.Inspect.stats
    # stats: stats: {'celery@e74ee63c3034': {'total': {'orchestrator.tasks.findEnrollment_ENR': 1, 'orchestrator.tasks.deleteEnrollment_ENR': 1, 'orchestrator.tasks.deletePerson_PR': 1, 'orchestrator.tasks.deleteAll_ABIS': 1, 'orchestrator.tasks.done': 1}, 'pid': 7, 'clock': '67', 'uptime': 65, 'pool': {'implementation': 'celery.concurrency.prefork:TaskPool', 'max-concurrency': 12, 'processes': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21], 'max-tasks-per-child': 'N/A', 'put-guarded-by-semaphore': False, 'timeouts': [0, 0], 'writes': {'total': 5, 'avg': '0.50', 'all': '0.60, 0.40', 'raw': '3, 2', 'strategy': 'fair', 'inqueues': {'total': 12, 'active': 0}}}, 'broker': {'hostname': 'redis', 'userid': None, 'virtual_host': '1', 'port': 6379, 'insist': False, 'ssl': False, 'transport': 'redis', 'connect_timeout': 4, 'transport_options': {}, 'login_method': None, 'uri_prefix': None, 'heartbeat': 120.0, 'failover_strategy': 'round-robin', 'alternates': [], 'credential_provider': None}, 'prefetch_count': 48, 'rusage': {'utime': 0.8181569999999999, 'stime': 0.652096, 'maxrss': 62988, 'ixrss': 0, 'idrss': 0, 'isrss': 0, 'minflt': 115966, 'majflt': 0, 'nswap': 0, 'inblock': 0, 'oublock': 24, 'msgsnd': 0, 'msgrcv': 0, 'nsignals': 0, 'nvcsw': 244, 'nivcsw': 41}}}
    for k,v in orchestrator.tasks.app.control.inspect().stats().items():
        stats = {}
        for k2, v2 in v['total'].items():
            stats[k2.split('.')[-1]] = v2
        return web.json_response(data=stats, status=200)
    return web.Response(status=500, body='')

