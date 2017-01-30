from unittest import TestCase

from hashdb2.command_line import main
from hashdb2.orm import create
from tempfile import TemporaryDirectory
from .generate_files import generate_files
import os.path
from sqlalchemy import MetaData, Table, func, and_

class TestHash(TestCase):
    def test_none(self):
        with TemporaryDirectory() as root:
            dbPath = os.path.join(root, 'hash.db')

            inputRoot = os.path.join(root, 'inputs')
            generate_files(inputRoot, True)

            main(['hash', '-n', dbPath, '--', os.path.join(inputRoot, 'b', 'y.txt'), os.path.join(inputRoot, 'e')])

            engine = create(dbPath)
            metadata = MetaData()
            Files = Table('Files', metadata, autoload=True, autoload_with=engine)

            for file in engine.execute(Files.select()):
                print(file)


