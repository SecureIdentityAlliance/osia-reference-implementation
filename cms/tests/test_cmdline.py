import unittest
from contextlib import redirect_stdout
import io

import cms
import cms.__main__


#_______________________________________________________________________________
class TestCmdLine(unittest.TestCase):

    def test_help(self):
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                cms.__main__.main(['-l','DEBUG', '-f', 'test.log', '--do-not-start'])
            except SystemExit:
                pass
        assert f.getvalue().find('do-not-start') > 0
