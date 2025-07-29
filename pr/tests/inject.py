
import base64
import sys
import os
import csv
import math
import random
import datetime
import time
import contextlib
import logging
import logging.config
import random, string
import http.server
import uuid
import json
import asyncio
import secrets

import aiohttp
from aiohttp import web
from aiojobs.aiohttp import setup, get_scheduler_from_app

import livemetrics
import livemetrics.publishers.aiohttp

__version__ = "1.0.0"

args = None
routes = web.RouteTableDef()

def is_healthy():
    return True
LM = livemetrics.LiveMetrics(json.dumps(dict(version=__version__)), "injector", is_healthy)

def ok_status(ret):
    return str(ret.status)

ELAPSE = 3.0
COUNT = 0

# _____________________________________________________________________________
def gauge_count():
    return COUNT
LM.gauge('count', gauge_count)

# _____________________________________________________________________________
def get_ssl_context():
    global args
    ctx = None
    if args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", args.server_certfile, args.server_keyfile)
        if args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(args.server_certfile,
                            args.server_keyfile,
                            password=args.server_keyfile_password)
        logging.debug("certfile/keyfile loaded for SSL Context")
    return ctx

# _____________________________________________________________________________
async def start_workers(app):
    global args
    # Create the workers
    elapse = 3600./args.rate
    nb_workers = 1
    if elapse<ELAPSE:
        nb_workers = int(math.ceil(ELAPSE/elapse))
        elapse = 3600.*nb_workers/args.rate
    if args.count>0:
        nb_workers = min(nb_workers,args.count)
        
    logging.info('Starting %d workers. Elapse: %.3f',nb_workers,elapse)
    sch = get_scheduler_from_app(app)
    for i in range(nb_workers):
        await sch.spawn(worker(f'worker-{i}'))
        await asyncio.sleep(elapse/nb_workers)
        logging.info(f'worker-{i} created')


# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=1024*1024)
    app.add_routes(routes)
    app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    setup(app, limit=1000)  # XXX set limit to the nb of workers
    return app

# _____________________________________________________________________________
def serve(args):
    app = get_app()
    app.on_startup.append(start_workers)
    logging.info('Starting application...')
    web.run_app(app, host=args.ip, port=args.port, access_log=None, ssl_context=get_ssl_context())
    logging.info('Closing application...')

# _____________________________________________________________________________
async def worker(name):
    global COUNT
    logging.info('Starting worker ' + name)
    while True:
        t0 = time.monotonic()
        if COUNT>=args.count:
            logging.info('Closing worker ' + name)
            return

        COUNT += 1
        logging.info("%s - injecting #%d", name, COUNT)
        # XXX shield
        # XXX catch exceptions, log and do not stop the worker
        await inject()

        if COUNT>=args.count:
            logging.info('Closing worker ' + name)
            return
        t1 = time.monotonic()
        delay = max(0.2, args.elapse - (t1 - t0))
        await asyncio.sleep(delay)
    logging.info('Closing worker ' + name)

def weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"

# _____________________________________________________________________________
async def inject():
    # build JSON
    today = datetime.datetime.today()
    age = random.betavariate(2, 5) * 80+15  # See https://fr.wikipedia.org/wiki/Loi_b%C3%AAta
    dob = today - datetime.timedelta(age*365.25)
    sx = random.randrange(0,2)
    if sx==0:
        gender = 'M'
        firstname = weighted_choice(firstnamesH)
    else:
        gender = 'F'
        firstname = weighted_choice(firstnamesF)
    lastname = weighted_choice(lastnames)[:50]

    # build UIN
    G = {'M':'1', 'F': '2'}.get(gender, '3')
    D = dob.strftime('%y%m%d')
    uin = G+D+''.join(secrets.choice('0123456789') for unused in range(5))

    tid = uuid.uuid4().hex
    async with aiohttp.ClientSession(base_url=args.url) as session:
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        async with session.post('v1/persons/'+uin, json=data, params={'transactionId': tid}, ssl=False ) as resp:
            assert 201 == resp.status

        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": firstname,
                "lastName": lastname,
                "gender": gender,
                "dateOfBirth": dob.date().isoformat()
            },
            "contextualData": {
                "operator": "OSIA",
                "operationDateTime": datetime.datetime.utcnow().isoformat(),
                "device": {
                    "name": "OSIA",
                    "brand": "SIA"
                }
            },
            "documentData": [
                {
                    "documentType": "FORM",
                    "parts": [
                        {
                            "pages": [
                                1
                            ],
                            "dataRef": "https://picsum.photos/200",
                            "mimeType": "image/jpeg",
                            "captureDate": "2019-05-21T12:00:00+02:00"
                        }
                    ]
                }
            ],
            "biometricData": [
                {
                    "biometricType": "FINGER",
                    "biometricSubType": "RIGHT_INDEX",
                    "imageRef": "https://picsum.photos/200",
                    "width": 500,
                    "height": 500,
                    "mimeType": "image/jpeg",
                    "missing": [
                        {
                            "biometricSubType": "RIGHT_INDEX",
                            "presence": "BANDAGED"
                        }
                    ]
                }
            ]
        }

        async with session.post('v1/persons/'+uin+'/identities/01', json=data, params={'transactionId': tid}, ssl=False ) as resp:
            assert 200 == resp.status
        async with session.put('v1/persons/'+uin+'/identities/01/reference', params={'transactionId': tid}, ssl=False ) as resp:
            assert 204 == resp.status

def main():
    global args
    import configargparse
    
    parser = configargparse.ArgumentParser(description='Injector')
    parser.add_argument("-l", "--loglevel",default='INFO',dest='loglevel',help="Log level (default: INFO)")
    parser.add_argument("-f", "--logfile",default="injector.log",dest='logfile',help="Log file (default: injector.log)")
    parser.add_argument("-u", "--url",action='store',default="http://localhost:8080/",dest='url',help="URL of the PR (default: http://localhost:8080/)")
    parser.add_argument("-i", "--ip",default='0.0.0.0',dest='ip',help="Listen IP (default: 0.0.0.0)")
    parser.add_argument("-P", "--port",default=None,dest='port',type=int,help="Port number (default: None)")
    parser.add_argument("-r", "--rate",action='store',default=3600,type=int,dest='rate',help="Injection rate (default: 3600/h)")
    parser.add_argument("-c", "--count",default=1,dest='count',type=int,help="Number of injection to be done. 0 for infinite. (default: 0)")
    parser.add_argument("-e", "--elapse",action='store',default="3",dest='elapse',type=float,help="Expected execution time")

    # arguments used for certificates
    parser.add_argument("--server-certfile", dest='server_certfile', env_var='PR_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying\nthis server')
    parser.add_argument("--server-keyfile", dest='server_keyfile', env_var='PR_KEYFILE',
                        default=None,
                        help='The private key identifying this server.')
    parser.add_argument("--server-keyfile-password", dest='server_keyfile_password',
                        env_var='PR_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key')
    parser.add_argument("--server-ca-certfile", dest='server_ca_certfile',
                        env_var='PR_CA_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificates of the clients for mutual authent')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',level=logging.getLevelName(args.loglevel))
    if args.logfile:
        fh = logging.handlers.TimedRotatingFileHandler(args.logfile,when='H',interval=8)
        fh.setLevel(logging.getLevelName(args.loglevel))
        formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)

    global firstnamesF, firstnamesH, lastnames
    firstnamesF = [(x[0],int(float(x[1]))) for x in csv.reader(open(os.path.join(os.path.split(__file__)[0],'alphadata/firstnameF.txt'),'r'))]
    firstnamesH = [(x[0],int(float(x[1]))) for x in csv.reader(open(os.path.join(os.path.split(__file__)[0],'alphadata/firstnameM.txt'),'r'))]
    lastnames = [(x[0],int(x[1])) for x in csv.reader(open(os.path.join(os.path.split(__file__)[0],'alphadata/lastname.txt'),'r'),delimiter='\t')]

    T0 = time.monotonic()

    serve(args)
    T1 = time.monotonic()
    delta = datetime.timedelta(seconds=(T1-T0))
    logging.info("Sent %d records in %s (%d errors reported)",COUNT,delta,0)
    
if __name__=='__main__':
    main()
