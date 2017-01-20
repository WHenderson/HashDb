from unittest import TestCase

from hashdb2.command_line import main
from docopt import DocoptExit
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

class TestCommand(TestCase):
    def test_help(self):
        with self.assertRaises(DocoptExit) as context:
            main([])
        self.assertTrue('Usage' in context.exception.usage)

    def test_version(self):
        with self.assertRaises(SystemExit) as context:
            out = StringIO()
            with redirect_stdout(out):
                main(['--version'])

        self.assertTrue('HashDb' in out.getvalue())
