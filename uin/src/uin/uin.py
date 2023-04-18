import ssl
import logging
import json
import secrets

import aiohttp
from aiohttp import web

import uin

import livemetrics
import livemetrics.publishers.aiohttp

routes = web.RouteTableDef()

def is_healthy():
    return True

LM = livemetrics.LiveMetrics(json.dumps(dict(version=uin.__version__)), "uin", is_healthy)

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
    if uin.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", uin.args.server_certfile, uin.args.server_keyfile)
        if uin.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", uin.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=uin.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(uin.args.server_certfile,
                            uin.args.server_keyfile,
                            password=uin.args.server_keyfile_password)
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
    site = web.TCPSite(runner, host=uin.args.ip, port=uin.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=uin.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    app.add_routes(routes)
    if uin.args.monitoring_port<=0 or uin.args.monitoring_port==uin.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if uin.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=uin.args.ip, port=uin.args.port, access_log=None, ssl_context=get_ssl_context())


#______________________________________________________________________________
@routes.post('/v1/uin')
@LM.timer("generateUIN", ok_status, "error")
async def generateUIN(request):
    transaction_id = request.query['transactionId']
    logging.info('[%s] - generateUIN', transaction_id)
    data = await request.json()

    G = {'M':'1', 'F': '2'}.get(data.get('gender','M'), '3')
    D = data.get('dateOfBirth','2000-01-01').replace('-','')[2:6]    # Note: not extensive tests on the format of the date
    uin = G+D+''.join(secrets.choice('0123456789') for unused in range(5))
    logging.info('[%s] - UIN generated: %s', transaction_id, uin)
    return web.json_response(data=uin, status=200)

