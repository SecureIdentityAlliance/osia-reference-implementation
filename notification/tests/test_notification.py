import unittest
import sys
import time
import json
import logging

import aiohttp
from aiohttp import web

import requests

import notification.notification

URL = "http://localhost:8000/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestNotification(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestNotification

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw


#_______________________________________________________________________________
class TestNominal(TestNotification):
    
    def test_topic(self):
        # Create a topic
        with requests.post(self.url+"v1/topics",params={'name':'TEST01'}) as r:
            assert r.status_code == 200
            assert r.json()['name']=='TEST01'
            T = r.json()

        # List the topics
        with requests.get(self.url+"v1/topics") as r:
            assert r.status_code == 200
            assert len(r.json())==1
            assert r.json()[0]['name']=="TEST01"

        # Create the same topic (idempotent)
        with requests.post(self.url+"v1/topics",params={'name':'TEST01'}) as r:
            assert r.status_code == 200
            assert r.json()['name']=='TEST01'
            assert r.json()['uuid']==T['uuid']

        # List the topics (no change)
        with requests.get(self.url+"v1/topics") as r:
            assert r.status_code == 200
            assert len(r.json())==1
            assert r.json()[0]['name']=="TEST01"

        # Delete the topic
        with requests.delete(self.url+"v1/topics/"+T['uuid']) as r:
            assert r.status_code == 204

        # List  the topics
        with requests.get(self.url+"v1/topics") as r:
            assert r.status_code == 200
            assert len(r.json())==0

        # Delete the same topic (error)
        with requests.delete(self.url+"v1/topics/"+T['uuid']) as r:
            assert r.status_code == 404

    
    def test_notification(self):
        # Create a topic
        with requests.post(self.url+"v1/topics",params={'name':'TEST01'},**get_ssl_context()) as r:
            assert r.status_code == 200
            assert r.json()['name']=='TEST01'
            T = r.json()

        # Subscribe with an invalid protocol
        with requests.post(self.url+"v1/subscriptions",params={'topic':'TEST01', 'protocol':'email', 'address': 'john.doe@gmail.com'}) as r:
            assert r.status_code == 400
            assert r.json()['code']==1

        # Subscribe with an invalid policy
        with requests.post(self.url+"v1/subscriptions",params={'topic':'TEST01', 'address': self.url+'test', 'policy': '-3,10'}) as r:
            assert r.status_code == 400
            assert r.json()['code']==2

        # Subscribe
        with requests.post(self.url+"v1/subscriptions",params={'topic':'TEST01', 'address': self.url+'test', 'policy': '3,10'}) as r:
            assert r.status_code == 200
            assert r.json()['protocol']=='http'
            S = r.json()

        # XXX could start the server after to test the retry mechanisms
        time.sleep(1.0)

        # Publish an event to a non existing topic
        with requests.post(self.url+"v1/topics/"+'non-existing-uuid'+"/publish",params={'subject':'SUBJECT'},data="test message") as r:
            assert r.status_code == 404

        # Publish an event
        with requests.post(self.url+"v1/topics/"+T['uuid']+"/publish",params={'subject':'SUBJECT'},data="test message") as r:
            assert r.status_code == 200

        time.sleep(1.0)

        assert self.MESSAGE['subject']=='SUBJECT'
        assert self.MESSAGE['message']=='test message'

        # Unsubscribe
        with requests.delete(self.url+"v1/subscriptions/"+S['uuid']) as r:
            assert r.status_code == 204

        # Unsubscribe (error)
        with requests.delete(self.url+"v1/subscriptions/"+S['uuid']) as r:
            assert r.status_code == 404

        # Publish again and make sure we get nothing - test publishing to a name (not a uuid)
        self.MESSAGE = None
        with requests.post(self.url+"v1/topics/TEST01/publish",params={'subject':'SUBJECT2'},data="test message2") as r:
            assert r.status_code == 200

        time.sleep(1.0)
        assert self.MESSAGE is None




if __name__ == '__main__':
    unittest.main(argv=['-v'])

