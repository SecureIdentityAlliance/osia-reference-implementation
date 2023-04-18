
"""
Bootstrap mocks used for unit tests
"""

import unittest
import time
import threading
import asyncio
import os
import base64
import json
import logging

from aiohttp import web

import notification
import notification.__main__
import notification.notification

LOOP = None
PORT = '8080'

async def runner():
    # Setup the global args variable (from the env variables)
    notification.__main__.main(['--do-not-start'])
    app = notification.notification.get_app()
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, 'localhost', int(PORT), reuse_address=True, ssl_context=notification.notification.get_ssl_context())
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
class TestNotification(unittest.TestCase):

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
        if notification.args.server_certfile:
            return "https://localhost:"+PORT+"/"
        else:
            return "http://localhost:"+PORT+"/"

    @property
    def mon_url(self):
        if int(os.environ.get('NOTIFICATION_MONITORING_PORT', 0))>0:
            return "http://localhost:"+os.environ.get('NOTIFICATION_MONITORING_PORT')+"/"
        else:
            if notification.args.server_certfile:
                return "https://localhost:"+PORT+"/"
            else:
                return "http://localhost:"+PORT+"/"

