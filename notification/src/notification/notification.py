import ssl
import logging
import json

import aiohttp
from aiohttp import web
import redis

import notification
import notification.tasks

import livemetrics
import livemetrics.publishers.aiohttp

routes = web.RouteTableDef()

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
    if notification.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", notification.args.server_certfile, notification.args.server_keyfile)
        if notification.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", notification.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=notification.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(notification.args.server_certfile,
                            notification.args.server_keyfile,
                            password=notification.args.server_keyfile_password)
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
    site = web.TCPSite(runner, host=notification.args.ip, port=notification.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=notification.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    app.add_routes(routes)
    if notification.args.monitoring_port<=0 or notification.args.monitoring_port==notification.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)
    app.on_startup.append(start_redis)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if notification.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=notification.args.ip, port=notification.args.port, access_log=None, ssl_context=get_ssl_context())

# _____________________________________________________________________________

# Connect to redis server
import os
import urllib
import uuid
import base64

R = None

async def start_redis(app):
    global R
    parts = urllib.parse.urlparse(notification.args.redis_url)
    R = redis.Redis(host=parts.hostname, port=parts.port or 6379, db=0)

def is_healthy():
    try:
        if R.ping():
            return True
    except:
        pass
    return False

LM = livemetrics.LiveMetrics(json.dumps(dict(version=notification.__version__)), "notification", is_healthy)

def ok_status(ret):
    return str(ret.status)

def gauge_topic():
    if R:
        return R.llen('TOPICS')
LM.gauge('topics',gauge_topic)

def gauge_subscription():
    if R:
        return R.llen('SUBSCRIPTIONS')
LM.gauge('subscriptions',gauge_subscription)


def s_encode(subscription):
    return json.dumps(subscription)

def s_decode(subscription):
    return json.loads(subscription)

def t_encode(topic):
    return json.dumps(topic)

def t_decode(topic):
    return json.loads(topic)

# _____________________________________________________________________________
# Subscriber services
# _____________________________________________________________________________

# _____________________________________________________________________________
@routes.post('/v1/subscriptions')
@LM.timer("subscribe", ok_status, "error")
async def subscribe(request):
    topic = request.query['topic']
    protocol = request.query.get('protocol', 'http')
    address = request.query['address']
    policy = request.query.get('policy', '3600,168')

    logging.info("Subscribe for [%s] for %s", topic, address)

    # Check input parameters
    if protocol != 'http':
        return web.json_response(dict(code=1, message="Invalid protocol (only http is supported in this implementation)"), status=400)

    try:
        countdown,max = [int(x) for x in policy.split(',')]
        if countdown<0:
            raise Exception()
    except:
        return web.json_response(dict(code=2, message="Invalid policy. Excepting 2 integers, first one must be positive"), status=400)

    # check if already there
    for s_idx in range(R.llen('SUBSCRIPTIONS')):
        s = s_decode(R.lindex('SUBSCRIPTIONS',s_idx))
        if s['topic']==topic and s['address']==address and s['protocol']==protocol:
            LM.mark("subscribe","ALREADY")
            return web.json_response(s, status=200)

    # New subscription
    s = dict(uuid=str(uuid.uuid1()),topic=topic, address=address, protocol=protocol, policy=policy,active=False)
    R.lpush('SUBSCRIPTIONS',s_encode(s))

    # Generate token & ask for confirmation
    token = base64.b64encode(json.dumps({'uuid': s['uuid'], 'address': s['address']}).encode('UTF-8')).decode('ascii')
    notification.tasks.request_confirmation.delay(s['protocol'],s['address'],token,topic,s['uuid'], s['policy'])
    LM.mark("subscribe","OK")

    return web.json_response(s, status=200)

# _____________________________________________________________________________
@routes.get('/v1/subscriptions')
@LM.timer("listSubscription", ok_status, "error")
async def listSubscription(request):
    logging.info("List subscriptions")

    S = []
    for s_idx in range(R.llen('SUBSCRIPTIONS')):
        s = s_decode(R.lindex('SUBSCRIPTIONS',s_idx))
        S.append(s)
    return web.json_response(S, status=200)

# _____________________________________________________________________________
@routes.delete('/v1/subscriptions/{uuid}')
@LM.timer("unsubscribe", ok_status, "error")
async def unsubscribe(request):
    id = request.match_info['uuid']
    logging.info("Unsubscribe for [%s]", id)

    for s_idx in range(R.llen('SUBSCRIPTIONS')):
        s = s_decode(R.lindex('SUBSCRIPTIONS',s_idx))
        if s['uuid'] == id:
            R.lrem('SUBSCRIPTIONS',0,R.lindex('SUBSCRIPTIONS',s_idx))
            LM.mark("unsubscribe","OK")
            return web.Response(status=204, body="")
    LM.mark("unsubscribe","ERROR")
    return web.Response(status=404, body="")


# _____________________________________________________________________________
@routes.get('/v1/subscriptions/confirm')
@LM.timer("confirm", ok_status, "error")
async def confirm(request):
    token = request.query['token']
    logging.info("Confirm subscription for token [%s]", token)

    try:
        token = json.loads(base64.b64decode(token).decode('UTF-8'))
    except:
        return web.json_response(dict(code=1, message="Invalid token"), status=400)

    for s_idx in range(R.llen('SUBSCRIPTIONS')):
        s = s_decode(R.lindex('SUBSCRIPTIONS',s_idx))
        if s['uuid']==token['uuid'] and s['address']==token['address']:
            if not s['active']:
                # Activate the subscription & save
                s['active'] = True
                R.lset('SUBSCRIPTIONS',s_idx,s_encode(s))
            return web.Response(status=200, body="")
    return web.json_response(dict(code=2, message="Invalid token"), status=400)

# _____________________________________________________________________________
# Publisher services
# _____________________________________________________________________________

# _____________________________________________________________________________
@routes.post('/v1/topics')
@LM.timer("createTopic", ok_status, "error")
async def createTopic(request):
    name = request.query['name']

    logging.info("Create topic [%s]", name)

    for t_idx in range(R.llen('TOPICS')):
        t = t_decode(R.lindex('TOPICS',t_idx))
        if t['name'] == name:
            LM.mark("createTopic","ALREADY")
            return web.json_response(t, status=200)
    t = dict(uuid=str(uuid.uuid1()), name=name)
    LM.mark("createTopic","OK")
    R.lpush('TOPICS',t_encode(t))
    logging.debug("Topic <%s> created (uuid: %s)",name,t['uuid'])
    return web.json_response(t, status=200)


# _____________________________________________________________________________
@routes.get('/v1/topics')
@LM.timer("listTopics", ok_status, "error")
async def listTopics(request):
    logging.info("List topics")

    T = []
    for t_idx in range(R.llen('TOPICS')):
        T.append( t_decode(R.lindex('TOPICS',t_idx)) )
    return web.json_response(T, status=200)


# _____________________________________________________________________________
@routes.delete('/v1/topics/{uuid}')
@LM.timer("deleteTopic", ok_status, "error")
async def deleteTopic(request):
    id = request.match_info['uuid']
    logging.info("Delete topic [%s]", id)

    # XXX should delete all subscriptions???
    for t_idx in range(R.llen('TOPICS')):
        t = t_decode(R.lindex('TOPICS',t_idx))
        if t['uuid'] == id:
            R.lrem('TOPICS',0,R.lindex('TOPICS',t_idx))
            LM.mark("deleteTopic","OK")
            return web.Response(status=204, body="")
    LM.mark("deleteTopic","ERROR")
    return web.Response(status=404, body="")


# _____________________________________________________________________________
@routes.post('/v1/topics/{uuid}/publish')
@LM.timer("publish", ok_status, "error")
async def publish(request):
    id = request.match_info['uuid']
    subject = request.query.get('subject', '')
    logging.info("Publish on topic [%s]", id)

    body = await request.read()
    body = body.decode('latin-1')

    for t_idx in range(R.llen('TOPICS')):
        t = t_decode(R.lindex('TOPICS',t_idx))
        if t['uuid']==id or t['name']==id:
            break
    else:
        LM.mark("publish","ERROR")
        return web.Response(status=404, body="")

    for s_idx in range(R.llen('SUBSCRIPTIONS')):
        s = s_decode(R.lindex('SUBSCRIPTIONS',s_idx))
        if s['active'] and (s['topic']==t['name'] or s['topic']==t['uuid']):
            notification.tasks.notify.delay(s['protocol'],s['address'],subject,body,t['uuid'], s['uuid'],s['policy'])
            LM.mark("publish","OK")
    return web.Response(status=200, body="")

# _____________________________________________________________________________
# *** Used for tests only ***
MESSAGE = None
@routes.post('/test')
async def CB(request):
    body = await request.read()
    m = json.loads(body.decode('utf-8'))

    if m['type']=='SubscriptionConfirmation':
        logging.info("Confirming subscription")
        logging.info(str(m))
        async with aiohttp.ClientSession() as clt_session:
            async with clt_session.get(m['subscribe_url'], ssl=False) as response:
                if response.status == 200:
                    await response.read()
                else:
                    logging.error("Failed to confirm subscription %s", m['subscribe_url'])
                    return web.Response(status=400, body='')
    else:
        logging.info("Notification")
        logging.info(str(m))
        global MESSAGE
        MESSAGE = m
    return web.Response(status=200, body='')
