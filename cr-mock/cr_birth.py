import sys
import logging
import argparse
import asyncio
import threading
import datetime

import requests

import aiohttp
from aiohttp import web

args = None
routes = web.RouteTableDef()

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

LOOP = None
PORT = '8080'

async def runner():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', int(PORT), reuse_address=True)
    await site.start()

def run_server(handler, args):
    global LOOP
    global PORT
    PORT = args.port
    loop = asyncio.new_event_loop()
    LOOP = loop
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handler)

    try:
        logging.info('Starting...')
        loop.run_forever()

    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

FN = None
# _____________________________________________________________________________
@routes.get('/v1/persons/{uin}')
async def readPersonAttributes(request):
    uin = request.match_info['uin']
    names = request.query.getall('attributeNames', [])

    logging.info("readPersonAttributes for UIN [%s]", uin)

    dob = datetime.date.today().isoformat()
    data = {
        "firstName": FN,
        "lastName": "Smith",
        "dateOfBirth": dob,
        "gender": "M",
        "nationality": "FRA",
    }

    ret = {}
    for k in names:
        if k in data:
            ret[k] = data[k]
    return web.json_response(ret, status=200)


def do_birth(args):

    global FN
    FN = args.firstname
    
    # match mother
    data = {
        "firstName": "Alice",
        "lastName": "Smith",
    }
    with requests.post(args.pr_url+'v1/persons/B/match', json=data,**get_ssl_context()) as r:
        assert 200 == r.status_code
        assert [] == r.json()
    logging.info("Mother data is OK (no error)")

    # match father
    data = {
        "firstName": "Albert",
        "lastName": "Smith",
    }
    with requests.post(args.pr_url+'v1/persons/A/match', json=data,**get_ssl_context()) as r:
        assert 200 == r.status_code
        assert [] == r.json()
    logging.info("Father data is OK (no error)")

    # read mother attributes
    params = {
        "attributeNames": ["dateOfBirth"]
    }
    with requests.get(args.pr_url+'v1/persons/B', params=params,**get_ssl_context()) as r:
        assert 200 == r.status_code
        assert {"dateOfBirth": "1987-11-30"} == r.json()
    logging.info("Get additional mother data")

    # read father attributes
    params = {
        "attributeNames": ["dateOfBirth"]
    }
    with requests.get(args.pr_url+'v1/persons/A', params=params,**get_ssl_context()) as r:
        assert 200 == r.status_code
        assert {"dateOfBirth": "1985-11-30"} == r.json()
    logging.info("Get additional father data")

    # check if new born exists
    dob = datetime.date.today().isoformat()
    params = {
        "firstName": args.firstname,
        "lastName": "Smith",
        "dateOfBirth": dob
    }
    with requests.get(args.pr_url+'v1/persons', params=params,**get_ssl_context()) as r:
        assert 200 == r.status_code
        if len(r.json()) > 0:
            logging.info("New born already in database")
            return
        assert [] == r.json()
    logging.info("New born not found in database")

    # get a new UIN for the child
    data = {
        "firstName": args.firstname,
        "lastName": "Smith",
        "dateOfBirth": dob,
        "gender": "M"
    }
    with requests.post(args.uin_url+'v1/uin', json=data, params={'transactionId': 'birth'},**get_ssl_context()) as r:
        assert 200 == r.status_code
        assert 'Server' not in r.headers
        UIN = r.json()
        assert '125' == UIN[:3]
    logging.info("UIN for child: %s", UIN)

    data = {
        "source": "CR-mock",
        "uin": UIN,
        "uin1": "A",
        "uin2": "B"
    }
    with requests.post(args.notification_url+"v1/topics/CR/publish",params={'subject':'liveBirth'},json=data) as r:
        assert r.status_code == 200
    logging.info("Notification sent")


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(description='CR mock')
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', help="Log level")
    parser.add_argument("-f", "--logfile", default=None, dest='logfile', help="Log file")
    parser.add_argument("-i", "--ip", default='0.0.0.0', dest='ip', help="Listen IP")
    parser.add_argument("-p", "--port", default=8080, dest='port', type=int, help="Port number")

    parser.add_argument("--pr-url", dest='pr_url',
                        default='http://localhost:8010/',
                        help='The URL to the PR service')
    parser.add_argument("--uin-url", dest='uin_url',
                        default='http://localhost:8020/',
                        help='The URL to the UIN generator service')
    parser.add_argument("--notification-url", dest='notification_url',
                        default='http://localhost:8030/',
                        help='The URL to the notification service')
    parser.add_argument("--fn", default='Baby', dest='firstname', help="First name of the baby")

    args = parser.parse_args(argv)

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',    # NOSONAR
                        level=logging.getLevelName(args.loglevel))
    if args.logfile:
        fh = logging.handlers.RotatingFileHandler(args.logfile, maxBytes=1000000, backupCount=20)
        fh.setLevel(logging.getLevelName(args.loglevel))
        formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)


    t = threading.Thread(target=run_server, args=(runner(), args), daemon=True)
    t.start()

    do_birth(args)

    input('Press enter to close')

if __name__ == '__main__':
    main()

