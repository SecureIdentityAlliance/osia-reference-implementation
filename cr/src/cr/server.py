import ssl
import logging
import json

import aiohttp
from aiohttp import web



import cr


import livemetrics
import livemetrics.publishers.aiohttp



# [---CUSTO---]
# Additional imports
import asyncio
# [---CUSTO---]

routes = web.RouteTableDef()

if 'is_healthy' not in globals():
    def is_healthy():
        return True

if 'is_ready' not in globals():
    def is_ready():
        return True

LM = livemetrics.LiveMetrics(json.dumps(dict(version=cr.__version__)), "cr", is_healthy, is_ready)

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
    if cr.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", cr.args.server_certfile, cr.args.server_keyfile)
        if cr.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", cr.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=cr.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(cr.args.server_certfile,
                            cr.args.server_keyfile,
                            password=cr.args.server_keyfile_password)
        logging.debug("certfile/keyfile loaded for SSL Context")
    return ctx

  
#______________________________________________________________________________
def get_notification_client_ssl_context():
    ctx = False
    if cr.args.notification_ca_certfile:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cr.args.notification_ca_certfile)
        logging.debug("notification SSL Context setup for CA FILE: %s", cr.args.notification_ca_certfile)

        if cr.args.notification_certfile:
            ctx.load_cert_chain(cr.args.notification_certfile,
                                keyfile=cr.args.notification_keyfile,
                                password=cr.args.notification_keyfile_password)
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
            logging.debug("certfile/keyfile loaded for SSL Context [%s, %s]", cr.args.notification_certfile, cr.args.notification_keyfile)
    return ctx

#______________________________________________________________________________
def get_pr_client_ssl_context():
    ctx = False
    if cr.args.pr_ca_certfile:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cr.args.pr_ca_certfile)
        logging.debug("pr SSL Context setup for CA FILE: %s", cr.args.pr_ca_certfile)

        if cr.args.pr_certfile:
            ctx.load_cert_chain(cr.args.pr_certfile,
                                keyfile=cr.args.pr_keyfile,
                                password=cr.args.pr_keyfile_password)
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
            logging.debug("certfile/keyfile loaded for SSL Context [%s, %s]", cr.args.pr_certfile, cr.args.pr_keyfile)
    return ctx

#______________________________________________________________________________
def get_uin_client_ssl_context():
    ctx = False
    if cr.args.uin_ca_certfile:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cr.args.uin_ca_certfile)
        logging.debug("uin SSL Context setup for CA FILE: %s", cr.args.uin_ca_certfile)

        if cr.args.uin_certfile:
            ctx.load_cert_chain(cr.args.uin_certfile,
                                keyfile=cr.args.uin_keyfile,
                                password=cr.args.uin_keyfile_password)
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
            logging.debug("certfile/keyfile loaded for SSL Context [%s, %s]", cr.args.uin_certfile, cr.args.uin_keyfile)
    return ctx

#______________________________________________________________________________
def get_enrollment_client_ssl_context():
    ctx = False
    if cr.args.enrollment_ca_certfile:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cr.args.enrollment_ca_certfile)
        logging.debug("enrollment SSL Context setup for CA FILE: %s", cr.args.enrollment_ca_certfile)

        if cr.args.enrollment_certfile:
            ctx.load_cert_chain(cr.args.enrollment_certfile,
                                keyfile=cr.args.enrollment_keyfile,
                                password=cr.args.enrollment_keyfile_password)
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
            logging.debug("certfile/keyfile loaded for SSL Context [%s, %s]", cr.args.enrollment_certfile, cr.args.enrollment_keyfile)
    return ctx


# _____________________________________________________________________________
async def _strip_server(req, res):
    if 'Server' in res.headers:
        del res.headers['Server']


# _____________________________________________________________________________
async def start_monitoring(app):
    app2 = web.Application(middlewares=[error_middleware])
    app2.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    if cr.args.loglevel=='DEBUG':
        runner = web.AppRunner(app2)
    else:
        runner = web.AppRunner(app2, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=cr.args.ip, port=cr.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=cr.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    if 'on_startup' in globals():
        app.on_startup.append(on_startup)
    if 'on_shutdown' in globals():
        app.on_shutdown.append(on_shutdown)
    app.add_routes(routes)
    if cr.args.monitoring_port<=0 or cr.args.monitoring_port==cr.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if cr.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=cr.args.ip, port=cr.args.port, access_log=None, ssl_context=get_ssl_context())





# [---CUSTO---]

PERSONS = {}

# _____________________________________________________________________________
@routes.get('/v1/persons/{uin}')
@LM.timer("readPersonAttributes", ok_status, "error")
async def readPersonAttributes(request):
    uin = request.match_info['uin']
    names = request.query.getall('attributeNames', [])
    logging.info("readPersonAttributes for UIN [%s]", uin)

    if not names:
        return web.json_response(dict(code=2, message="No names specified"), status=400)

    p = PERSONS.get(uin, None)
    if not p:
        return web.Response(status=404)
    ident_data = p

    obj = {}
    for k in names:
        if k in ident_data['biographicData']:
            obj[k] = ident_data['biographicData'][k]
        elif k in ident_data['contextualData']:
            obj[k] = ident_data['contextualData'][k]
        elif k in ident_data:
            obj[k] = ident_data[k]
    return web.json_response(obj, status=200)

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
        event = json.loads(m['message'])
        await execute(event)
    return web.Response(status=200, body='')

# _____________________________________________________________________________
async def on_startup(app):
    if cr.args.do_not_start:
        return
    logging.info("Register for events from topic [enrollment]")
    params = {'topic':'enrollment', 'address': cr.args.my_url+'enrollment_event', 'policy': '3,10'}

    N = 20
    while N>0:
        try:
            await asyncio.sleep(5)
            N -= 10
            async with aiohttp.ClientSession() as clt_session:
                async with clt_session.post(cr.args.notification_url+"v1/topics", params={'name':'enrollment'}, ssl=get_notification_client_ssl_context()) as response:
                    if response.status == 200:
                        await response.read()
                    else:
                        logging.error("Failed to create topic [enrollment]")
                        continue
                async with clt_session.post(cr.args.notification_url+"v1/subscriptions", params=params, ssl=get_notification_client_ssl_context()) as response:
                    if response.status == 200:
                        await response.read()
                        break
                    else:
                        logging.error("Failed to subscribe on topic [enrollment]")
        except:
            logging.error("Could not subscribe on topic enrollment")


# _____________________________________________________________________________
async def execute(event):
    enrollment_id = event['enrollmentId']
    transaction_id = event['transactionId']
    logging.info(f"[{transaction_id}] - Receiving new enrollment [{enrollment_id}]")
    async with aiohttp.ClientSession() as clt_session:
        # (6) read the enrollment from the enrollment server
        async with clt_session.get(cr.args.enrollment_url+"v1/enrollments/"+enrollment_id, params={'transactionId': transaction_id}, ssl=get_notification_client_ssl_context()) as response:
            if response.status == 200:
                enr = await response.json()
            else:
                logging.error(f"[{transaction_id}] - Enrollment not found for id {enrollment_id}")
                return
        logging.info("[%s] - Enrollment [%s] for [%s]/[%s]" % (transaction_id, enrollment_id, enr['biographicData']['firstName'], enr['biographicData']['lastName']) )

        # (7) read parent's attribute to establish the birth certificate
        params = {
            "attributeNames": ["firstName", "lastName", "dateOfBirth", "gender"]
        }
        async with clt_session.get(cr.args.pr_url+"v1/persons/"+enr['biographicData']['parentUIN'], params=params, ssl=get_pr_client_ssl_context()) as response:
            if response.status == 200:
                parent = await response.json()
            else:
                logging.error(f"[{transaction_id}] - Parent data not found for UIN {enr['biographicData']['parentUIN']}")
                return
        logging.info(f"[{transaction_id}] - Retrieved the parent's data: {parent['firstName']} {parent['lastName']}")

        # (8) Check child does not exist in PR
        params = {
            "firstName": enr['biographicData']['firstName'],
            "lastName": enr['biographicData']['lastName'],
            "dateOfBirth": enr['biographicData']['dateOfBirth']
        }
        async with clt_session.get(cr.args.pr_url+"v1/persons", params=params, ssl=get_pr_client_ssl_context()) as response:
            if response.status == 200:
                candidates = await response.json()
                if len(candidates)>0:
                    logging.error(f"[{transaction_id}] - Child is already in the databases - Stopping the process")
                    return
            else:
                logging.error(f"[{transaction_id}] - Error checking in PR if the child is already registered")
                return
        logging.info(f"[{transaction_id}] - Child not found in database")

        # (9) generate a new UIN for the child
        data = {
            "firstName": enr['biographicData']['firstName'],
            "lastName": enr['biographicData']['lastName'],
            "dateOfBirth": enr['biographicData']['dateOfBirth'],
            "gender": enr['biographicData']['gender']
        }
        async with clt_session.post(cr.args.uin_url+"v1/uin", json=data, params={'transactionId': transaction_id}, ssl=get_uin_client_ssl_context()) as response:
            if response.status == 200:
                enr['biographicData']['UIN'] = await response.json()
            else:
                logging.error(f"[{transaction_id}] - Unable to generate a new UIN for the child")
                return

        # Fake registration of child in the CR
        PERSONS[enr['biographicData']['UIN']] = dict(
            biographicData=enr['biographicData'],
            contextualData=enr['contextualData'],
        )
        logging.info(f"[{transaction_id}] - Child is registered in this CR (UIN={enr['biographicData']['UIN']})")

        # (10) Publish event of new birth registration
        data = {
            "source": "CR",
            "uin": enr['biographicData']['UIN'],
            "uin1": enr['biographicData']['parentUIN'],
            "uin2": "",
            "transactionId": transaction_id,
            "enrollmentId": enrollment_id
        }
        async with clt_session.post(cr.args.notification_url+"v1/topics/CR/publish", json=data, params={'subject':'liveBirth'}, ssl=get_notification_client_ssl_context()) as response:
            if response.status == 200:
                logging.info(f"[{transaction_id}] - END - notification of liveBirth published")
            else:
                logging.error(f"[{transaction_id}] - END - Unable to send notification of liveBirth")
                return


# [---CUSTO---]
