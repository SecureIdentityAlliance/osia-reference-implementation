import unittest
from contextlib import redirect_stdout
import io

import uin
import uin.__main__


#_______________________________________________________________________________
class TestCmdLine(unittest.TestCase):

    def test_help(self):
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                uin.__main__.main(['-l','DEBUG', '-f', 'test.log', '--do-not-start'])
            except SystemExit:
                pass
        assert f.getvalue().find('do-not-start') > 0

