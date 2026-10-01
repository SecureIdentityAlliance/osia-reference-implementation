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

    class TestCr(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestCr

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

# [---CUSTO---]
#_______________________________________________________________________________
class TestNominal(TestCr):
    def test_ok(self):
        with requests.get(self.url+'v1/persons/P0002', params={'attributeNames': ['firstName', 'lastName', 'missing']}, **get_ssl_context()) as r:
            assert 404 == r.status_code


# [---CUSTO---]

if __name__ == '__main__':
    unittest.main(argv=['-v'])
