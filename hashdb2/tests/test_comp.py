from unittest import TestCase

from hashdb2.command_line import main
from hashdb2.orm import create
from tempfile import TemporaryDirectory
from .generate_files import generate_files, generate_structure, structures
import os.path
from sqlalchemy import MetaData, Table, func, and_
from hashdb2.hash import HASHBLOCK_QUICK

class TestComp(TestCase):
    def test_structures(self):
        with generate_structure(structures['complex']) as root:
            dbLhs = os.path.join(root, 'lhs.db')
            dbRhs = os.path.join(root, 'rhs.db')
            #inputRoot = os.path.join(root, 'inputs')

            main(['comp', '--lhs-db', dbLhs, '--rhs-db', dbRhs, '--', 'echo', '{LHS}', '{RHS}'])




