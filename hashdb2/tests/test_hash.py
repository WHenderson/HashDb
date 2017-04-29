from unittest import TestCase

from hashdb2.command_line import main
from hashdb2.orm import create
from tempfile import TemporaryDirectory
from .generate_files import generate_files, generate_structure, structures
import os.path
from sqlalchemy import MetaData, Table, func, and_
from hashdb2.hash import HASHBLOCK_QUICK

class TestHash(TestCase):
    def test_structures(self):
        for hashMode in ['-n', '-q', '-f']:
            for name, structure in structures.items():
                with generate_structure(structure) as root:
                    dbPath = os.path.join(root, 'hash.db')
                    inputRoot = os.path.join(root, 'inputs')

                    main(['hash', hashMode, dbPath, '--', inputRoot])

                    engine = create(dbPath)
                    metadata = MetaData()
                    Files = Table('Files', metadata, autoload=True, autoload_with=engine)

                    def hash_quick(file):
                        if (hashMode == '-q') or (hashMode == '-f') or file.data == None or len(file.data) == 0:
                            return file.hash_quick
                        return None
                    def hash_total(file):
                        if (hashMode == '-q' and len(file.data) <= HASHBLOCK_QUICK*3) or (hashMode == '-f') or file.data == None or len(file.data) == 0:
                            return file.hash_total
                        return None

                    inputFiles = [
                        (os.path.normpath(file.path), os.path.basename(file.path), os.path.splitext(file.path)[1], len(file.data), file.time, hash_quick(file), hash_total(file))
                        for file in structure if isinstance(file.data, bytes) or isinstance(file.data, bytearray)
                    ]
                    inputFiles.sort()
                    outputFiles = [
                        (os.path.normpath(os.path.relpath(file.path, root)), os.path.basename(file.path), os.path.splitext(file.path)[1], file.size, file.time, file.hash_quick, file.hash_total)
                        for file in engine.execute(Files.select())
                    ]
                    outputFiles.sort()

                    print('#', hashMode, name)
                    for file in outputFiles:
                        print(file)

                    try:
                        self.assertEqual(inputFiles, outputFiles)
                    except Exception as ex:
                        raise ex


