from unittest import TestCase

from hashdb2.command_line import main
from hashdb2.orm import create
from tempfile import TemporaryDirectory
from .generate_files import generate_structure, structures, FileInfo
import os.path
from sqlalchemy import MetaData, Table, func, and_
from hashdb2.hash import HASHBLOCK_QUICK

structure_standard = [
    FileInfo('lhs', None, None, None, None),
    FileInfo('lhs/a0-file-no-extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('lhs/a0-file-with.extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('lhs/a1-file-with--64k-content', b'[ start....... ]' * (64 * 1024 // 16), 0, '64f1d479c57ad4c63ac0fe548fefc16c', '64f1d479c57ad4c63ac0fe548fefc16c'),
    FileInfo('lhs/a2-file-with-128k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16), 0, 'be8d3f4b5e419026509beb8b0aa14517', 'be8d3f4b5e419026509beb8b0aa14517'),
    FileInfo('lhs/a3-file-with-192k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16) + b'[ .........end ]' * (64 * 1024 // 16), 0, 'd77e9be5c1ecf730da5afaedd3d3048a', 'd77e9be5c1ecf730da5afaedd3d3048a'),
    FileInfo('lhs/a4-file-with-200k-nulls', b'\0' * 200 * 1024, 0, 'ef2e0d18474b2151ef5876b1e89c2f1d', 'c522c1db31cc1f90b5d21992fd30e2ab'),
    FileInfo('lhs/an-empty-folder', None, None, None, None),
    FileInfo('lhs/a-folder', None, None, None, None),
    FileInfo('lhs/a-folder/a0-file', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('lhs/a-link-to-a-file', 'inputs/a-folder/a-file', 0, None, None),
    FileInfo('lhs/a-link-to-a-folder', 'inputs/a-folder/', 0, None, None),
    FileInfo('lhs/a-bad-file-link', 'inputs/file-does-not-exist', 0, None, None),
    FileInfo('lhs/a-bad-folder-link', 'inputs/folder-does-not-exist/', 0, None, None),
    FileInfo('lhs/a-unique-file', b'lhs/a-unique-file', 0, None, None),
    FileInfo('lhs/another-unique-file', b'lhs/another-unique-file', 0, None, None),

    FileInfo('rhs', None, None, None, None),
    FileInfo('rhs/a0-file-no-extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('rhs/a0-file-with.extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('rhs/a1-file-with--64k-content', b'[ start....... ]' * (64 * 1024 // 16), 0, '64f1d479c57ad4c63ac0fe548fefc16c', '64f1d479c57ad4c63ac0fe548fefc16c'),
    FileInfo('rhs/a2-file-with-128k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16), 0, 'be8d3f4b5e419026509beb8b0aa14517', 'be8d3f4b5e419026509beb8b0aa14517'),
    FileInfo('rhs/a3-file-with-192k-content', b'[ start....... ]' * (64 * 1024 // 16) + b'[ ...middle... ]' * (64 * 1024 // 16) + b'[ .........end ]' * (64 * 1024 // 16), 0, 'd77e9be5c1ecf730da5afaedd3d3048a', 'd77e9be5c1ecf730da5afaedd3d3048a'),
    FileInfo('rhs/a4-file-with-200k-nulls', b'\0' * 200 * 1024, 0, 'ef2e0d18474b2151ef5876b1e89c2f1d', 'c522c1db31cc1f90b5d21992fd30e2ab'),
    FileInfo('rhs/an-empty-folder', None, None, None, None),
    FileInfo('rhs/a-folder', None, None, None, None),
    FileInfo('rhs/a-folder/a0-file', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    FileInfo('rhs/a-link-to-a-file', 'inputs/a-folder/a-file', 0, None, None),
    FileInfo('rhs/a-link-to-a-folder', 'inputs/a-folder/', 0, None, None),
    FileInfo('rhs/a-bad-file-link', 'inputs/file-does-not-exist', 0, None, None),
    FileInfo('rhs/a-bad-folder-link', 'inputs/folder-does-not-exist/', 0, None, None),
    FileInfo('rhs/a-unique-file', b'rhs/a-unique-file', 0, None, None),
    FileInfo('rhs/another-unique-file', b'rhs/another-unique-file', 0, None, None),
]

class TestComp(TestCase):
    def _execute_comp_all(self, args):
        with generate_structure(structure_standard) as root:
            dbLhs = os.path.join(root, 'all.db')

            results = []
            def capture(result):
                results.append(result)

            print('args:', ' '.join(args))

            main(['comp', '--lhs-db', dbLhs, '--lhs-path', root, '--'] + args, fcapture=capture)

            for result in results:
                for i in range(len(result)):
                    result[i] = result[i].replace(root, '').replace('\\', '/')
                print(str(result) + ',')

            return results

    def _execute_comp_lhs_rhs(self, args):
        with generate_structure(structure_standard) as root:
            dbLhs = os.path.join(root, 'lhs.db')
            dbRhs = os.path.join(root, 'rhs.db')
            #inputRoot = os.path.join(root, 'inputs')

            results = []
            def capture(result):
                results.append(result)


            print('args:', ' '.join(args))

            main(['comp', '--lhs-db', dbLhs, '--lhs-path', os.path.join(root, 'lhs'), '--rhs-db', dbRhs, '--rhs-path', os.path.join(root, 'rhs'), '--'] + args, fcapture=capture)

            for result in results:
                for i in range(len(result)):
                    result[i] = result[i].replace(root, '').replace('\\', '/')
                print(str(result) + ',')

            return results

    def test_lhs(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHS}']),
            [
                ['/lhs/a-folder/a0-file'],
                ['/lhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_lhs_rhs(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHS}', '{RHS}']),
            [
                ['/lhs/a-folder/a0-file', '/rhs/a-folder/a0-file'],
                ['/lhs/a-folder/a0-file', '/rhs/a0-file-no-extension'],
                ['/lhs/a0-file-no-extension', '/rhs/a-folder/a0-file'],
                ['/lhs/a0-file-no-extension', '/rhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension', '/rhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content', '/rhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content', '/rhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content', '/rhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls', '/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_lhs_rhsgroup(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHS}', '{RHSGROUP}']),
            [
                ['/lhs/a-folder/a0-file', '/rhs/a-folder/a0-file,/rhs/a0-file-no-extension'],
                ['/lhs/a0-file-no-extension', '/rhs/a-folder/a0-file,/rhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension', '/rhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content', '/rhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content', '/rhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content', '/rhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls', '/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_lhsgroup(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHSGROUP}']),
            [
                ['/lhs/a-folder/a0-file,/lhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_lhsgroup_rhs(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHSGROUP}', '{RHS}']),
            [
                ['/lhs/a-folder/a0-file,/lhs/a0-file-no-extension', '/rhs/a-folder/a0-file'],
                ['/lhs/a-folder/a0-file,/lhs/a0-file-no-extension', '/rhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension', '/rhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content', '/rhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content', '/rhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content', '/rhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls', '/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_lhsgroup_rhsgroup(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHSGROUP}', '{RHSGROUP}']),
            [
                ['/lhs/a-folder/a0-file,/lhs/a0-file-no-extension', '/rhs/a-folder/a0-file,/rhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension', '/rhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content', '/rhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content', '/rhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content', '/rhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls', '/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_lhsonly(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHSONLY}']),
            [
                ['/lhs/a-unique-file'],
                ['/lhs/another-unique-file'],
            ]
        )

    def test_lhsonlygroup(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{LHSONLYGROUP}']),
            [
                ['/lhs/a-unique-file,/lhs/another-unique-file'],
            ]
        )

    def test_rhs(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{RHS}']),
            [
                ['/rhs/a-folder/a0-file'],
                ['/rhs/a0-file-no-extension'],
                ['/rhs/a0-file-with.extension'],
                ['/rhs/a1-file-with--64k-content'],
                ['/rhs/a2-file-with-128k-content'],
                ['/rhs/a3-file-with-192k-content'],
                ['/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_rhsgroup(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{RHSGROUP}']),
            [
                ['/rhs/a-folder/a0-file,/rhs/a0-file-no-extension'],
                ['/rhs/a0-file-with.extension'],
                ['/rhs/a1-file-with--64k-content'],
                ['/rhs/a2-file-with-128k-content'],
                ['/rhs/a3-file-with-192k-content'],
                ['/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_rhsonly(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{RHSONLY}']),
            [
                ['/rhs/a-unique-file'],
                ['/rhs/another-unique-file'],
            ]
        )

    def test_rhsonlygroup(self):
        self.assertEqual(
            self._execute_comp_lhs_rhs(['{RHSONLYGROUP}']),
            [
                ['/rhs/a-unique-file,/rhs/another-unique-file'],
            ]
        )

    def test_dupe(self):
        self.assertEqual(
            self._execute_comp_all(['{DUPE}']),
            [
                ['/lhs/a-folder/a0-file'],
                ['/lhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls'],
                ['/rhs/a-folder/a0-file'],
                ['/rhs/a0-file-no-extension'],
                ['/rhs/a0-file-with.extension'],
                ['/rhs/a1-file-with--64k-content'],
                ['/rhs/a2-file-with-128k-content'],
                ['/rhs/a3-file-with-192k-content'],
                ['/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_dupegroup(self):
        self.assertEqual(
            self._execute_comp_all(['{DUPEGROUP}']),
            [
                ['/lhs/a-folder/a0-file,/lhs/a0-file-no-extension,/rhs/a-folder/a0-file,/rhs/a0-file-no-extension'],
                ['/lhs/a0-file-with.extension,/rhs/a0-file-with.extension'],
                ['/lhs/a1-file-with--64k-content,/rhs/a1-file-with--64k-content'],
                ['/lhs/a2-file-with-128k-content,/rhs/a2-file-with-128k-content'],
                ['/lhs/a3-file-with-192k-content,/rhs/a3-file-with-192k-content'],
                ['/lhs/a4-file-with-200k-nulls,/rhs/a4-file-with-200k-nulls'],
            ]
        )

    def test_unique(self):
        self.assertEqual(
            self._execute_comp_all(['{UNIQUE}']),
            [
                ['/all.db'],
                ['/lhs/a-unique-file'],
                ['/lhs/another-unique-file'],
                ['/rhs/a-unique-file'],
                ['/rhs/another-unique-file'],
            ]
        )


    def test_uniquegroup(self):
        self.assertEqual(
            self._execute_comp_all(['{UNIQUEGROUP}']),
            [
                ['/all.db,/lhs/a-unique-file,/lhs/another-unique-file,/rhs/a-unique-file,/rhs/another-unique-file'],
            ]
        )
