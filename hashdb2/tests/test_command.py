from unittest import TestCase

from hashdb2.command_line import main
from docopt import DocoptExit

class TestCommand(TestCase):
    def test_help(self):
        with self.assertRaises(DocoptExit) as context:
            main([])
        self.assertTrue('Usage' in context.exception.usage)

    def test_version(self):
        with self.assertRaises(SystemExit) as context:
            main(['--version'])
