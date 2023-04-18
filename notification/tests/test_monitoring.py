import unittest
import sys

import requests

URL = "http://localhost:8080/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestNotification(unittest.TestCase):

        @property
        def mon_url(self):
            global URL
            return URL

else:
    from . import TestNotification

#_______________________________________________________________________________
class TestNominal(TestNotification):
    def test_health(self):
        with requests.get(self.mon_url+'monitoring/v1/is_healthy', verify=False) as r:
            assert 200 == r.status_code



if __name__ == '__main__':
    unittest.main(argv=['-v'])
