#!/usr/bin/python
import os as OS
import os.path as PATH
import sys as SYS
import stat as STAT

import hashdb_path as PATHPARTS
import hashdb_mntent_wrapper as MOUNTS

mounts = MOUNTS.MountEntries()

iterpath = PATHPARTS.iterpath

def rootpath(truepath, binds=False):
    return mounts.rootpath(truepath, binds=binds)

def is_mount(truepath):
    return mounts.is_mount(truepath)
        
def is_sysmount(path):
    return mounts.is_sysmount(path)
        
def truepath(path):
    return mounts.truepath(path)

def stat(path):
    try:
        return OS.lstat(path)
    except OSError, ex:
        return None

def uniqueid(path, stat):
    return (stat.st_dev, stat.st_ino)
   
def is_dir(stat):
    return STAT.S_ISDIR(stat.st_mode)
    
def is_lnk(stat):
    return STAT.S_ISLNK(stat.st_mode)
   
def is_reg(stat):
    return STAT.S_ISREG(stat.st_mode)
    
    
if __name__ == '__main__':
    print list(PATHPARTS.iterpath('w:\\'))
    print list(PATHPARTS.iterpath('w:\\parta\\partb\\partc.txt'))
    print list(PATHPARTS.iterpath('/'))
    print list(PATHPARTS.iterpath('/parta/partb/partc.txt'))