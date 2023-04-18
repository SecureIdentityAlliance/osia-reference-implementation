import unittest
import sys

import requests

URL = "http://localhost:8080/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestUin(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestUin

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

#_______________________________________________________________________________
class TestNominal(TestUin):
    def test_ok(self):
        data = {
            "firstName": "Albert",
            "lastName": "Smith",
            "dateOfBirth": "1985-11-30",
            "gender": "M",
            "nationality": "FRA",
        }

        # Nominal case
        with requests.post(self.url+'v1/uin', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 'Server' not in r.headers
            assert '18511' == r.json()[:5]


if __name__ == '__main__':
    unittest.main(argv=['-v'])

