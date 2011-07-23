#!/usr/bin/python

import os as OS
import os.path as PATH
import sys as SYS
import random as RANDOM

def main(base):
    base = PATH.realpath(base)

    build_basic(PATH.join(base, 'basic'))
    
    if SYS.platform != 'win32':
        build_linkloop(PATH.join(base, 'linkloop'))

def create_dirs(base, dirs):
    for dir in dirs:
        OS.makedirs(PATH.join(base, dir))
        
def create_files(base, files):
    for file in files:
        fps = [open(PATH.join(base, name), 'wb') for name in file[0]]
        
        for x in xrange(file[1]):
            data = ''.join(RANDOM.choice("0123456789abcdef") for x in xrange(1024))
            for fp in fps:
                fp.write(data)
        
        for fp in fps:
            fp.close()

def create_links(base, links):
    for dst, src in links:
        OS.symlink(src, PATH.join(base, dst))

def build_basic(base):
    create_dirs(base, [
        '1',
        '2',
        '3'
    ])
    
    from itertools import product
    files = []
    for i,x in enumerate(product((0,1), repeat=3)):
        if x == (0,0,0):
            continue
        filenames = []
        of = ''.join('%d' % (column + 1) for column, include in enumerate(x) if include)
        for column,include in enumerate(x):
            if include:
                filenames.append('%s/%s_in_%s_of_%s.txt' % (column + 1, 'abcdefghijklmnopqrstuvwxyz'[i - 1], column + 1, of))
        print filenames
        files.append((tuple(filenames), 160))
    
    create_files(base, files)

def build_linkloop(base):
    create_dirs(base, [
        'a',
        'a/a1',
        'b',
        'b/b1'
    ])
    create_links(base, [
        ('a/a1/linkto_b', '../../b'),
        ('b/b1/linkto_a', '../../a'),
    ])
    create_files(base, [
        (('a/a.txt',), 4),
        (('b/b.txt',), 4),
    ])

if __name__ == '__main__':
    if len(SYS.argv) != 2:
        print 'please specify a directory'
        exit(-1)
        
    main(SYS.argv[1])