#!/usr/bin/python
from hashdb_fs import truepath, stat, is_lnk, is_dir, uniqueid, mounts
import os as OS
import os.path as PATH
import hashdb_fs as FS
from collections import namedtuple, deque

UserTarget   = namedtuple('UserTarget', 'userpath abspath depth')
TrueTarget   = namedtuple('TrueTarget', 'truepath stat usertargets userdata')

def doyield(truetarget):
    return True
def skip_base(parent, basename, userdata):
    '''parent is a TrueTarget, basename as seen from the userpath'''
    return False
def skip_path(parent, path, userdata):
    '''parent is a TrueTarget, path is an absolute user path'''
    return False
def skip_stats(parent, path, stats, usertargets, userdata):
    '''parent is a TrueTarget, path is a truepath, stat is the stat for the truepath and usertargets is an (authoritative) list of UserTarget's relating to this truepath'''
    return False
def sort(filenames):
    filenames.sort()
    return filenames

def walk(targets, ftruepath=truepath, fstat=stat, fis_lnk=is_lnk, fis_dir=is_dir, funiqueid=uniqueid, fsort=sort, fdoyield=None, fskip_base=None, fskip_path=None, fskip_stats=None, depthfirst=True):
    # turn all incoming targets into TrueTarget's
    roots = {}
    for userpath in targets:
        userpath = PATH.normpath(userpath)
        abspath  = PATH.abspath(userpath)
        truepath = ftruepath(userpath)
        if truepath == None:
            continue

        # stat the path
        stat = fstat(truepath)
        if stat == None:
            continue

        # find unique id for the path
        uniqueid = funiqueid(truepath, stat)
        if uniqueid == None:
            continue

        # merge the new root target in
        if uniqueid in roots:
            roots[uniqueid].usertargets.append(UserTarget(userpath, abspath, 0))
        else:
            roots[uniqueid] = TrueTarget(truepath, stat, [UserTarget(userpath, abspath, 0)], {})

    # nothing to do?
    if len(roots) == 0:
        return
    
    # create a sorted list of roots (sorted based on truepath, and in reverse)
    roots_sorted = list(((k,),v) for k,v in roots.iteritems())
    roots_sorted.sort(key=lambda x: x[1].truepath, reverse=True)
    
    # start with nothing remaining
    remaining = deque()
    
    # Perform the tree walk
    while True:
        # Grab the next TrueTarget
        try:
            stats, uniqueids, truetarget = remaining.popleft()
        except IndexError, _:
            try:
                uniqueids, truetarget = roots_sorted.pop()
                roots.pop(uniqueids[0])
                stats = tuple(fstat(path) for path in FS.iterpath(truetarget.truepath))
            except IndexError, _:
                break
            except OSError, _:
                continue
            except IOError, _:
                continue
            
        #print ' root:', truetarget.truepath, uniqueids
        
        # yield?
        if (fdoyield == None) or fdoyield(truetarget):
            yield truetarget

        # is dir?
        if fis_dir(truetarget.stat):
            # list contents
            try:
                filelist = OS.listdir(truetarget.truepath)
                filelist = fsort(filelist)
            except OSError, _:
                continue
            
            # go through the entire list
            remaining_filelist = []
            for base in filelist:
                userdata = {}
                
                # skip base?
                if (fskip_base != None) and fskip_base(truetarget, base, userdata):
                    continue
                
                # usertargets
                usertargets = []
                for usertarget in truetarget.usertargets:
                    # skip path?
                    abspath = PATH.join(usertarget.abspath, base)
                    if (fskip_path != None) and fskip_path(abspath, abspath, userdata):
                        continue
                    
                    usertargets.append(UserTarget(PATH.join(usertarget.userpath, base), abspath, usertarget.depth + 1))
                # nothing to do?
                if len(usertargets) == 0:
                    continue
                
                # truepath
                truepath = PATH.join(truetarget.truepath, base)
                
                # stat
                stat = fstat(truepath)
                if stat == None:
                    continue
                newstats = stats + (stat,)
                
                # skip stat?
                if (fskip_stats != None) and fskip_stats(truetarget, truepath, stat, usertargets, userdata):
                    continue
                
                uniqueid = funiqueid(truepath, stat)
                if uniqueid == None:
                    continue
                newuniqueids = uniqueids + (uniqueid,)

                # is link?        
                if fis_lnk(stat) or mounts.is_bindmount(truepath):
                    # find the true path of this link
                    newtruepath = ftruepath(truepath)
                    if newtruepath == None:
                        continue
                    if newtruepath != truepath:
                        truepath = newtruepath
                        
                        stat = fstat(truepath)
                        if stat == None:
                            continue

                        # get unique id for this node
                        uniqueid = funiqueid(newtruepath, stat)
                        if uniqueid == None:
                            continue
                        # recursive loop?
                        if uniqueid in newuniqueids:
                            continue
                        
                        # skip stat?
                        if (fskip_stats != None) and fskip_stats(truetarget, truepath, stat, usertargets, userdata):
                            continue
                        
                        newstats = newstats + (stat,)
                        newuniqueids = newuniqueids + (uniqueid,)
                   
                # identical to an existing root?
                if uniqueid in roots:
                    root = roots.pop(uniqueid)
                    roots_sorted.remove(((uniqueid,), root))
                    usertargets.extend(root.usertargets)
    
                # compile list of files
                remaining_filelist.append((newstats, newuniqueids, TrueTarget(truepath, stat, usertargets, userdata)))

            # queue item according to depth ordering                    
            if depthfirst:
                remaining_filelist.sort(key=lambda x: (fis_dir(x[2].stat), x[2].truepath), reverse=True)
                remaining.extendleft(remaining_filelist)
            else:
                remaining_filelist.sort(key=lambda x: (fis_dir(x[2].stat), x[2].truepath))
                remaining.extend(remaining_filelist)
        # is anything else?
        else:
            continue
        
        
if __name__ == '__main__':
    import sys as SYS
    
    for truetarget in walk(SYS.argv[1:]):
        print truetarget.truepath
        for usertarget in truetarget.usertargets:
            print ' %s' % usertarget.userpath
