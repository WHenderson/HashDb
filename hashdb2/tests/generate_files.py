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

FileInfo = namedtuple('File', ('path', 'data', 'time'))

structures = {
    'non-existent': [],
    'empty': [
        FileInfo('inputs', None, None),
    ],
    'single-file': [
        FileInfo('inputs', None, None),
        FileInfo('inputs/only-file.txt', b'some content', 0),
    ],
    'single-folder': [
        FileInfo('inputs', None, None),
        FileInfo('inputs/only-folder', None, 0),
    ],
    'complex': [
        FileInfo('inputs', None, None),
        FileInfo('inputs/a-file-no-extension', b'', 0),
        FileInfo('inputs/a-file-with.extension', b'', 0),
        FileInfo('inputs/a-file-with--64k-content', b'[ start....... ]'*(64*1024//16), 0),
        FileInfo('inputs/a-file-with-128k-content', b'[ start....... ]'*(64*1024//16) + b'[ ...middle... ]'*(64*1024//16), 0),
        FileInfo('inputs/a-file-with-192k-content', b'[ start....... ]'*(64*1024//16) + b'[ ...middle... ]'*(64*1024//16) + b'[ .........end ]'*(64*1024//16), 0),
        FileInfo('inputs/a-file-with-200k-nulls', b'\0'*200*1024, 0),
        FileInfo('inputs/an-empty-folder', None, None),
        FileInfo('inputs/a-folder', None, None),
        FileInfo('inputs/a-folder/a-file', b'', 0),
        FileInfo('inputs/a-link-to-a-file', 'inputs/a-folder/a-file', 0),
        FileInfo('inputs/a-link-to-a-folder', 'inputs/a-folder/', 0),
        FileInfo('inputs/a-bad-file-link', 'inputs/file-does-not-exist', 0),
        FileInfo('inputs/a-bad-folder-link', 'inputs/folder-does-not-exist/', 0),
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
