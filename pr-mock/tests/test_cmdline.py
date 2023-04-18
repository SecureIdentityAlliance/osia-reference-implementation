import unittest
from contextlib import redirect_stdout
import io

import pr
import pr.__main__


#_______________________________________________________________________________
class TestCmdLine(unittest.TestCase):

    def test_help(self):
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                pr.__main__.main(['-l','DEBUG', '-f', 'test.log', '--do-not-start'])
            except SystemExit:
                pass
        assert f.getvalue().find('do-not-start') > 0

