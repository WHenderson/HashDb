from unittest import TestCase

from hashdb2.command_line import main
from tempfile import TemporaryDirectory
from .generate_files import generate_files
import os.path
import sqlite3

class TestHash(TestCase):
    def test_none(self):
        with TemporaryDirectory() as root:
            dbPath = os.path.join(root, 'hash.db')

            inputRoot = os.path.join(root, 'inputs')
            generate_files(inputRoot, True)

            main(['hash', '-n', dbPath, '--', os.path.join(inputRoot, 'b', 'y.txt'), os.path.join(inputRoot, 'e')])

            #conn = sqlite3.connect(dbPath)


