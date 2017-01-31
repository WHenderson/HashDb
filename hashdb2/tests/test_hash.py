from unittest import TestCase

from hashdb2.command_line import main
from hashdb2.orm import create
from tempfile import TemporaryDirectory
from .generate_files import generate_files, generate_structure, structures
import os.path
from sqlalchemy import MetaData, Table, func, and_

class TestHash(TestCase):
    def test_structures(self):
        for name, structure in structures.items():
            with generate_structure(structure) as root:
                dbPath = os.path.join(root, 'hash.db')
                inputRoot = os.path.join(root, 'inputs')

                main(['hash', '-n', dbPath, '--', inputRoot])

                engine = create(dbPath)
                metadata = MetaData()
                Files = Table('Files', metadata, autoload=True, autoload_with=engine)

                inputFiles = [
                    (os.path.normpath(file.path), os.path.basename(file.path), os.path.splitext(file.path)[1], len(file.data), file.time, None, None)
                    for file in structure if isinstance(file.data, bytes) or isinstance(file.data, bytearray)
                ]
                inputFiles.sort()
                outputFiles = [
                    (os.path.normpath(os.path.relpath(file.path, root)), os.path.basename(file.path), os.path.splitext(file.path)[1], file.size, file.time, None, None)
                    for file in engine.execute(Files.select())
                ]
                outputFiles.sort()


                self.assertEqual(inputFiles, outputFiles)

