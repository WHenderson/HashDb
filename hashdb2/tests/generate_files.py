import os
import os.path
from collections import namedtuple
from contextlib import contextmanager
from tempfile import TemporaryDirectory

def generate_files(root, createRoot=False):
    if createRoot:
        os.mkdir(root)

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

FileInfo = namedtuple('File', ('path', 'data', 'time', 'hash_quick', 'hash_total'))

structures = {
    'non-existent': [],
    'empty': [
        FileInfo('inputs', None, None, None, None),
    ],
    'single-file': [
        FileInfo('inputs', None, None, None, None),
        FileInfo('inputs/only-file.txt', b'some content', 0, '9893532233caff98cd083a116b013c0b', '9893532233caff98cd083a116b013c0b'),
    ],
    'single-folder': [
        FileInfo('inputs', None, None, None, None),
        FileInfo('inputs/only-folder', None, 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
    ],
    'complex': [
        FileInfo('inputs', None, None, None, None),
        FileInfo('inputs/a-file-no-extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
        FileInfo('inputs/a-file-with.extension', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
        FileInfo('inputs/a-file-with--64k-content', b'[ start....... ]'*(64*1024//16), 0, '64f1d479c57ad4c63ac0fe548fefc16c', '64f1d479c57ad4c63ac0fe548fefc16c'),
        FileInfo('inputs/a-file-with-128k-content', b'[ start....... ]'*(64*1024//16) + b'[ ...middle... ]'*(64*1024//16), 0, 'be8d3f4b5e419026509beb8b0aa14517', 'be8d3f4b5e419026509beb8b0aa14517'),
        FileInfo('inputs/a-file-with-192k-content', b'[ start....... ]'*(64*1024//16) + b'[ ...middle... ]'*(64*1024//16) + b'[ .........end ]'*(64*1024//16), 0, 'd77e9be5c1ecf730da5afaedd3d3048a', 'd77e9be5c1ecf730da5afaedd3d3048a'),
        FileInfo('inputs/a-file-with-200k-nulls', b'\0'*200*1024, 0, 'ef2e0d18474b2151ef5876b1e89c2f1d', 'c522c1db31cc1f90b5d21992fd30e2ab'),
        FileInfo('inputs/an-empty-folder', None, None, None, None),
        FileInfo('inputs/a-folder', None, None, None, None),
        FileInfo('inputs/a-folder/a-file', b'', 0, 'd41d8cd98f00b204e9800998ecf8427e', 'd41d8cd98f00b204e9800998ecf8427e'),
        FileInfo('inputs/a-link-to-a-file', 'inputs/a-folder/a-file', 0, None, None),
        FileInfo('inputs/a-link-to-a-folder', 'inputs/a-folder/', 0, None, None),
        FileInfo('inputs/a-bad-file-link', 'inputs/file-does-not-exist', 0, None, None),
        FileInfo('inputs/a-bad-folder-link', 'inputs/folder-does-not-exist/', 0, None, None),
    ],
}

@contextmanager
def generate_structure(files):
    with TemporaryDirectory() as root:
        for file in files:
            targetPath = os.path.join(root, file.path)
            if file.data is None:
                os.mkdir(targetPath)
                continue
            elif isinstance(file.data, bytes) or isinstance(file.data, bytearray):
                with open(os.path.join(root, file.path), 'wb') as fp:
                    fp.write(file.data)

                try:
                    os.utime(targetPath, ns=(file.time, file.time), follow_symlinks=False)
                except NotImplementedError:
                    os.utime(targetPath, ns=(file.time, file.time))

            elif isinstance(file.data, str):
                sourcePath = os.path.join(root, file.data)
                is_dir = sourcePath.endswith('/')
                if is_dir:
                    sourcePath = sourcePath[:-1]
                #print('%s : %s', targetPath, os.path.relpath(sourcePath, targetPath))
                os.symlink(os.path.relpath(sourcePath, os.path.dirname(targetPath)), targetPath, is_dir)


        yield root
