from unittest import TestCase
from tempfile import TemporaryDirectory
import os.path

from hashdb2.walk import walk

def deepEqual(lhs, rhs):
    if lhs == rhs:
        return True

    if (isinstance(lhs, list) and isinstance(rhs, list)) or (isinstance(lhs, tuple) and isinstance(rhs, tuple)):
        l = len(lhs)
        if len(rhs) != l:
            return False

        for i in range(l):
            if not deepEqual(lhs[i], rhs[i]):
                return False

        return True

    return False

class TestWalk(TestCase):
    def test_walk(self):
        with TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, 'a'))
            os.mkdir(os.path.join(root, 'b'))
            os.mkdir(os.path.join(root, 'c'))
            os.mkdir(os.path.join(root, 'c', 'd'))
            os.mkdir(os.path.join(root, 'e'))
            os.mkdir(os.path.join(root, 'e', 'f'))

            with open(os.path.join(root, 'x.txt'), 'wb'):
                pass
            with open(os.path.join(root, 'b', 'y.txt'), 'wb'):
                pass
            with open(os.path.join(root, 'e', 'f', 'z.txt'), 'wb'):
                pass

            def relativePaths(paths):
                return sorted(os.path.relpath(p.path, root) for p in paths)

            topDown = [(os.path.relpath(top, root), relativePaths(dirs), relativePaths(nondirs)) for top, dirs, nondirs in walk(root)]
            bottomUp = [(os.path.relpath(top, root), relativePaths(dirs), relativePaths(nondirs)) for top, dirs, nondirs in walk(root, False)]
            single = [(os.path.relpath(top, root), relativePaths(dirs), relativePaths(nondirs)) for top, dirs, nondirs in walk(os.path.join(root, 'x.txt'))]

            topDown.sort()
            bottomUp.sort()

            self.assertTrue(deepEqual(topDown, [
                ('.', ['a', 'b', 'c', 'e'], ['x.txt']),
                ('a', [], []),
                ('b', [], [os.path.join('b', 'y.txt')]),
                ('c', [os.path.join('c', 'd')], []),
                (os.path.join('c', 'd'), [], []),
                ('e', [os.path.join('e', 'f')], []),
                (os.path.join('e', 'f'), [], [os.path.join('e', 'f', 'z.txt')])
            ]))

            self.assertTrue(deepEqual(bottomUp, [
                ('.', ['a', 'b', 'c', 'e'], ['x.txt']),
                ('a', [], []),
                ('b', [], [os.path.join('b', 'y.txt')]),
                ('c', [os.path.join('c', 'd')], []),
                (os.path.join('c', 'd'), [], []),
                ('e', [os.path.join('e', 'f')], []),
                (os.path.join('e', 'f'), [], [os.path.join('e', 'f', 'z.txt')])
            ]))

            self.assertTrue(deepEqual(single, [
                ('.', [], ['x.txt'])
            ]))
