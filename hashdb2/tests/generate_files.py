import os
import os.path

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

