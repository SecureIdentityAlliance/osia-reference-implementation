
"""
Bootstrap mocks used for unit tests
"""

import unittest
import time
import threading
import asyncio
import os

from aiohttp import web

import pr
import pr.__main__

LOOP = None

# Setup the global args variable (from the env variables)
pr.__main__.main(['--do-not-start',
                '--port', '8080',
                '--custo-filename', os.path.join(os.path.dirname(__file__),'custo.yaml')])

import pr.server

async def runner():
    # Setup the global args variable (from the env variables)
    # we need to do it a second time in the server thread
    pr.__main__.main(['--do-not-start',
                    '--port', '8080',
                    # to increase test coverage if needed:
                    # '--loglevel', 'DEBUG',
                    # '--logfile', 'test.log',
                    '--custo-filename', os.path.join(os.path.dirname(__file__),'custo.yaml')])
    app = pr.server.get_app()
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, 'localhost', pr.args.port, reuse_address=True, ssl_context=pr.server.get_ssl_context())
    await site.start()

def run_server(handler):
    global LOOP
    loop = asyncio.new_event_loop()
    LOOP = loop
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handler)

    try:
        loop.run_forever()

    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

#_______________________________________________________________________________
class TestPR(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global LOOP
        # Create one test server only for the first test running. Will be reused for the other tests
        if LOOP: return
        cls.t = threading.Thread(target=run_server, args=(runner(),), daemon=True)
        cls.t.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        # Clean up to release the socket address for the other tests
        pass
        # global LOOP
        # LOOP.stop()

    @property
    def url(self):
        if pr.args.server_certfile:
            return "https://localhost:{}/".format(pr.args.port)
        else:
            return "http://localhost:{}/".format(pr.args.port)

    @property
    def mon_url(self):
        if pr.args.monitoring_port>0:
            return "http://localhost:{}/".format(pr.args.monitoring_port)
        else:
            if pr.args.server_certfile:
                return "https://localhost:{}/".format(pr.args.port)
            else:
                return "http://localhost:{}/".format(pr.args.port)

