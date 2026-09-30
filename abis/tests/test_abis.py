import unittest
import sys

import requests

# [---CUSTO---]
# [---CUSTO---]

URL = "http://localhost:8080/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestAbis(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestAbis

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

# [---CUSTO---]
#_______________________________________________________________________________
class TestNominal(TestAbis):

    def test_create(self):

        # Create encounter
        data = {
            "status":"ACTIVE",
            "encounterType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo"
            },
            "biometricData": [
                {
                    "biometricType": "FINGER",
                    "biometricSubType": "RIGHT_INDEX",
                    "image": "SU1BR0U=", # "IMAGE" base64-encoded
                    "width": 500,
                    "height": 500,
                    "mimeType": "image/png",
                    "missing": [
                        {
                            "biometricSubType": "RIGHT_INDEX",
                            "presence": "BANDAGED"
                        }
                    ]
                }
            ],
            "contextualData": {}
        }
        with requests.post(self.url+'v1/persons/P0001/encounters/001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['encounterId'] == '001'
            # assert list(res.keys()) == ['identityId']
            assert 'Server' not in r.headers

        # read the encounters
        with requests.get(self.url+'v1/persons/P0001/encounters', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1

    def test_verify_by_id(self):

        # Create encounter
        data = {
            "status":"ACTIVE",
            "encounterType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo"
            },
            "biometricData": [
                {
                    "biometricType": "FINGER",
                    "biometricSubType": "RIGHT_INDEX",
                    "image": "SU1BR0U=", # "IMAGE" base64-encoded
                    "width": 500,
                    "height": 500,
                    "mimeType": "image/png",
                    "missing": [
                        {
                            "biometricSubType": "RIGHT_INDEX",
                            "presence": "BANDAGED"
                        }
                    ]
                }
            ],
            "contextualData": {}
        }
        with requests.post(self.url+'v1/persons/P0002/encounters/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['encounterId'] == '001'
            assert 'Server' not in r.headers

        # verify
        data = {"biometricData": [
                {
                    "biometricType": "FINGER",
                    "biometricSubType": "RIGHT_INDEX",
                    "image": "SU1BR0U=", # "IMAGE" base64-encoded
                    "width": 500,
                    "height": 500,
                    "mimeType": "image/png",
                    "missing": [
                        {
                            "biometricSubType": "RIGHT_INDEX",
                            "presence": "BANDAGED"
                        }
                    ]
                }
            ]}
        with requests.post(self.url+'v1/verify/ALL/P0002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['decision'] == True
        with requests.post(self.url+'v1/verify/ALL/P0099', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['decision'] == False

# [---CUSTO---]

if __name__ == '__main__':
    unittest.main(argv=['-v'])
