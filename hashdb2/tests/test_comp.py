from unittest import TestCase

from hashdb2.command_line import main
from hashdb2.orm import create
from tempfile import TemporaryDirectory
from .generate_files import generate_files, generate_structure, structures, FileInfo
import os.path
from sqlalchemy import MetaData, Table, func, and_
from hashdb2.hash import HASHBLOCK_QUICK

structure_standard = [
    FileInfo('lhs', None, None, None, None),
    FileInfo('lhs/a-file-no-extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('lhs/a-file-with.extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('lhs/a-file-with--64k-content', b'[ start....... ]' * (64 * 1024 // 16), 0, '64f1d479c57ad4c63ac0fe548fefc16c', '64f1d479c57ad4c63ac0fe548fefc16c'),
    FileInfo('lhs/a-file-with-128k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16), 0, 'be8d3f4b5e419026509beb8b0aa14517', 'be8d3f4b5e419026509beb8b0aa14517'),
    FileInfo('lhs/a-file-with-192k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16) + b'[ .........end ]' * (64 * 1024 // 16), 0, 'd77e9be5c1ecf730da5afaedd3d3048a', 'd77e9be5c1ecf730da5afaedd3d3048a'),
    FileInfo('lhs/a-file-with-200k-nulls', b'\0' * 200 * 1024, 0, 'ef2e0d18474b2151ef5876b1e89c2f1d', 'c522c1db31cc1f90b5d21992fd30e2ab'),
    FileInfo('lhs/an-empty-folder', None, None, None, None),
    FileInfo('lhs/a-folder', None, None, None, None),
    FileInfo('lhs/a-folder/a-file', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('lhs/a-link-to-a-file', 'inputs/a-folder/a-file', 0, None, None),
    FileInfo('lhs/a-link-to-a-folder', 'inputs/a-folder/', 0, None, None),
    FileInfo('lhs/a-bad-file-link', 'inputs/file-does-not-exist', 0, None, None),
    FileInfo('lhs/a-bad-folder-link', 'inputs/folder-does-not-exist/', 0, None, None),

    FileInfo('rhs', None, None, None, None),
    FileInfo('rhs/a-file-no-extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('rhs/a-file-with.extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('rhs/a-file-with--64k-content', b'[ start....... ]' * (64 * 1024 // 16), 0, '64f1d479c57ad4c63ac0fe548fefc16c', '64f1d479c57ad4c63ac0fe548fefc16c'),
    FileInfo('rhs/a-file-with-128k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16), 0, 'be8d3f4b5e419026509beb8b0aa14517', 'be8d3f4b5e419026509beb8b0aa14517'),
    FileInfo('rhs/a-file-with-192k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16) + b'[ .........end ]' * (64 * 1024 // 16), 0, 'd77e9be5c1ecf730da5afaedd3d3048a', 'd77e9be5c1ecf730da5afaedd3d3048a'),
    FileInfo('rhs/a-file-with-200k-nulls', b'\0' * 200 * 1024, 0, 'ef2e0d18474b2151ef5876b1e89c2f1d', 'c522c1db31cc1f90b5d21992fd30e2ab'),
    FileInfo('rhs/an-empty-folder', None, None, None, None),
    FileInfo('rhs/a-folder', None, None, None, None),
    FileInfo('rhs/a-folder/a-file', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('rhs/a-link-to-a-file', 'inputs/a-folder/a-file', 0, None, None),
    FileInfo('rhs/a-link-to-a-folder', 'inputs/a-folder/', 0, None, None),
    FileInfo('rhs/a-bad-file-link', 'inputs/file-does-not-exist', 0, None, None),
    FileInfo('rhs/a-bad-folder-link', 'inputs/folder-does-not-exist/', 0, None, None),
]

class TestComp(TestCase):
    def test_structures(self):
        with generate_structure(structure_standard) as root:
            dbLhs = os.path.join(root, 'lhs.db')
            dbRhs = os.path.join(root, 'rhs.db')
            #inputRoot = os.path.join(root, 'inputs')

            main(['comp', '--lhs-db', dbLhs, '--lhs-path', 'lhs', '--rhs-db', dbRhs, '--rhs-path', 'rhs', '--', 'echo', '{LHS}', '{RHS}'])




