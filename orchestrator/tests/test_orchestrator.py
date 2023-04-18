import unittest
import sys

import requests

URL = "http://localhost:8080/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestOrchestrator(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestOrchestrator

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

#_______________________________________________________________________________
class TestNominal(TestOrchestrator):
    def test_ok(self):
        pass


if __name__ == '__main__':
    unittest.main(argv=['-v'])

