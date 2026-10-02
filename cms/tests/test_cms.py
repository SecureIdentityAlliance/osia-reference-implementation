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

    class TestCms(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestCms

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

# [---CUSTO---]
#_______________________________________________________________________________
class TestNominal(TestCms):
    def test_ok(self):
        data = {
        #    "status": "PENDING",
            "requestData": {
                "priority": 1,
                "credentialProfileId": "ID_CARD",
                "requestType": "FIRST_ISSUANCE",
                "validFromDate": "2026-10-02T12:00:00",
                "validToDate": "2031-10-01T12:00:00",
                "issuingAuthority": "OSIA",
            },
            "personId": "UIN",
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo",
                "dateOfBirth": "1985-11-30",
                "gender": "M",
                "nationality": "FRA",
            },
            "biometricData": [
                {
                    "biometricType": "FACE",
                    "image": "c3RyaW5n",
                }
            ]
        }
        
        # Nominal case
        with requests.post(self.url+'v1/credentialRequests/0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code
            assert 'Server' not in r.headers

    def test_error(self):
        data = dict(
            data1='error'
        )

        # Nominal case
        with requests.post(self.url+'v1/credentialRequests/0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 400 == r.status_code

# [---CUSTO---]

if __name__ == '__main__':
    unittest.main(argv=['-v'])
