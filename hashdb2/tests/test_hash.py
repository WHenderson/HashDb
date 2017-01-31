from unittest import TestCase

from hashdb2.command_line import main
from hashdb2.orm import create
from tempfile import TemporaryDirectory
from .generate_files import generate_files, generate_structure, structures
import os.path
from sqlalchemy import MetaData, Table, func, and_


class TestHash(TestCase):
    def test_none(self):
        with generate_structure(structures['complex']) as root:
            dbPath = os.path.join(root, 'hash.db')
            inputRoot = os.path.join(root, 'inputs')

            main(['hash', '-n', dbPath, '--', inputRoot])

            engine = create(dbPath)
            metadata = MetaData()
            Files = Table('Files', metadata, autoload=True, autoload_with=engine)

            for file in engine.execute(Files.select()):
                print(file)


