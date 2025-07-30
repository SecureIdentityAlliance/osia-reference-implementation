import unittest
import sys
import os
import base64

import requests
from requests_toolbelt.multipart import decoder

URL = "http://localhost:8080/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestPR(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestPR

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

#_______________________________________________________________________________
class TestDataAccess(TestPR):

    def setUp(self):
        # Insert test data
        # Create person1 with 1 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/DA001-1', json=data, params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/DA001-1/identities/001', json=data, params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create person2 with 2 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/DA001-2', json=data, params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnBA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/DA001-2/identities/001', json=data, params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        with requests.put(self.url+'v1/persons/DA001-2/identities/001/reference', params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTB"],
            "biographicData": {
                "firstName": "JohnBB",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/DA001-2/identities/002', json=data, params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 201 == r.status_code

    def tearDown(self):
        # delete the person
        with requests.delete(self.url+'v1/persons/DA001-1', params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.delete(self.url+'v1/persons/DA001-2', params={'transactionId': 'T000DA1'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_matchPersonAttributes(self):

        data = dict(
            firstName= "John",
            lastName= "Doo",
            missing= "Missing",
        )
        # bad UIN
        with requests.post(self.url+'v1/persons/DA001-UNKNOWN/match', json=data, **get_ssl_context()) as r:
            assert 404 == r.status_code
        # no reference identity
        with requests.post(self.url+'v1/persons/DA001-1/match', json=data, **get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.post(self.url+'v1/persons/DA001-2/match', json=data, **get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res)==2
            assert res == [
                {'attributeName':'firstName', 'errorCode': 1},
                {'attributeName':'missing', 'errorCode': 0},
            ]

    def test_queryPersonList(self):
        # good query, but no candidate
        with requests.get(self.url+'v1/persons', params={'firstName': 'John', 'names': ['firstName', 'lastName']},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res)==0

        # good query, one candidate
        with requests.get(self.url+'v1/persons', params={'firstName': 'JohnBA', 'names': ['firstName', 'lastName']},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res)==1
            assert res == [{
                'firstName': 'JohnBA',
                'lastName': 'Doo'
            }]

        # good query, one candidate, UIN only
        with requests.get(self.url+'v1/persons', params={'firstName': 'JohnBA', },**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res)==1
            assert res == ['DA001-2']

        # bad query
        with requests.get(self.url+'v1/persons', params={'undefined': 'JohnBA', },**get_ssl_context()) as r:
            assert 400 == r.status_code
            res = r.json()
            assert res['message'].find('undefined') > 0

    def test_readPersonAttributes(self):
        # good query, one candidate
        with requests.get(self.url+'v1/persons/DA001-2', params={'attributeNames': ['firstName', 'lastName', 'missing']},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res == {
                'firstName': 'JohnBA',
                'lastName': 'Doo',
                'missing': {
                    'code': 2,
                    'message': "Unknown attribute name [missing]"
                }
            }

        # bad query, no names specified
        with requests.get(self.url+'v1/persons/DA001-2', params={},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # good query, no reference identity
        with requests.get(self.url+'v1/persons/DA001-1', params={'attributeNames': ['firstName', 'lastName', 'missing']},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # good query, bad UIN
        with requests.get(self.url+'v1/persons/DA001-1-UNDEFINED', params={'attributeNames': ['firstName', 'lastName', 'missing']},**get_ssl_context()) as r:
            assert 404 == r.status_code

    def test_verifyPersonAttributes(self):
        data = [dict(
            attributeName="firstName",
            operator="=",
            value="JohnBA"
        )]
        # undef person
        with requests.post(self.url+'v1/persons/DA001-1-UNDEF/verify', json=data, **get_ssl_context()) as r:
            assert 404 == r.status_code
        # person with no reference identity
        with requests.post(self.url+'v1/persons/DA001-1/verify', json=data, **get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() is False
        # person with a reference identity
        with requests.post(self.url+'v1/persons/DA001-2/verify', json=data, **get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() is True
        data = [dict(
            attributeName="firstName",
            operator="=",
            value="John"
        )]
        with requests.post(self.url+'v1/persons/DA001-2/verify', json=data, **get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() is False

#_______________________________________________________________________________
class TestDataAccessDocument(TestPR):

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), 'DOCUMENT.pdf'), 'rb') as f:
            self.document = f.read()

        # Insert test data
        # Create person1 with 1 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/DA002-1', json=data, params={'transactionId': 'T000DA2'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doe"
            },
            "documentData": [
                {
                    "documentType": "FORM",
                    "parts": [
                        {
                            "pages": [
                                1
                            ],
                            "data": base64.b64encode(self.document).decode('ascii'),
                            "mimeType": "application/pdf",
                            "captureDate": "2019-05-21T12:00:00+02:00"
                        }
                    ]
                },
                {
                    "documentType": "PASSPORT",
                    "parts": [
                        {
                            "pages": [
                                1
                            ],
                            "data": base64.b64encode(b'DOCUMENT1').decode('ascii'),
                            "mimeType": "application/pdf",
                            "captureDate": "2019-05-21T12:00:00+02:00"
                        },
                        {
                            "pages": [
                                2
                            ],
                            "data": base64.b64encode(b'DOCUMENT2').decode('ascii'),
                            "mimeType": "application/pdf",
                            "captureDate": "2019-05-21T12:00:00+02:00"
                        },
                        {
                            "pages": [
                                3
                            ],
                            "dataRef": "https://picsum.photos/200",
                            "mimeType": "application/pdf",
                            "captureDate": "2019-05-21T12:00:00+02:00"
                        }
                    ]
                },
                {
                    "documentType": "INVOICE",
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
            ]
        }
        with requests.post(self.url+'v1/persons/DA002-1/identities/001', json=data, params={'transactionId': 'T000DA2'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        with requests.put(self.url+'v1/persons/DA002-1/identities/001/reference', params={'transactionId': 'T000DA2'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def tearDown(self):
        # delete the person
        with requests.delete(self.url+'v1/persons/DA002-1', params={'transactionId': 'T000DA2'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_readDocument(self):
        # test OK, one PDF returned
        with requests.get(self.url+'v1/persons/DA002-1/document', params={'doctype': 'FORM', 'format': 'pdf'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert self.document == r.content

        # test OK, 3 PDF returned in a multipart structure
        with requests.get(self.url+'v1/persons/DA002-1/document', params={'doctype': 'PASSPORT', 'format': 'pdf'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            mp = decoder.MultipartDecoder.from_response(r)
            assert 3 == len(mp.parts)
            assert b'DOCUMENT1' == mp.parts[0].content
            assert b'DOCUMENT2' == mp.parts[1].content
            assert b'https://picsum.photos/200' == mp.parts[2].content
            assert b"https://picsum.photos/200" == mp.parts[2].headers[b'Location']

        # test OK, dataRef as a redirect
        with requests.get(self.url+'v1/persons/DA002-1/document', params={'doctype': 'INVOICE', 'format': 'jpeg'},allow_redirects=False, **get_ssl_context()) as r:
            assert 302 == r.status_code
            assert 'https://picsum.photos/200' == r.headers['Location']

        # test UIN not found
        with requests.get(self.url+'v1/persons/DA002-1-NOTFOUND/document', params={'doctype': 'FORM', 'format': 'pdf'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # test missing parameter    
        with requests.get(self.url+'v1/persons/DA002-1/document', params={'doctype': 'FORM'},**get_ssl_context()) as r:
            assert 400 == r.status_code
        with requests.get(self.url+'v1/persons/DA002-1/document', params={'format': 'pdf'},**get_ssl_context()) as r:
            assert 400 == r.status_code
        with requests.get(self.url+'v1/persons/DA002-1/document', params={},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # tests secondaryUin (not supported)
        with requests.get(self.url+'v1/persons/DA002-1/document', params={'secondaryUin':'UIN2', 'doctype': 'FORM', 'format': 'pdf'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # test no doc
        with requests.get(self.url+'v1/persons/DA002-1/document', params={'doctype': 'ID_CARD', 'format': 'pdf'},**get_ssl_context()) as r:
            assert 404 == r.status_code

if __name__ == '__main__':
    unittest.main(argv=['-v'])

