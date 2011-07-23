import os as OS
import os.path as PATH
import sys as SYS

import hashdb_fs as FS
import hashdb_database as DB
import hashdb_database_duplicates as DBD
import hashdb_walk as WALK
import hashdb_hash as HASH
import hashdb_mntent_wrapper as MOUNTS
import hashdb_path as PATHPARTS

DATABASE_BASENAME = '.hashdb'

def sort(filenames):
    def name_cmp(lhs, rhs):
        if lhs == DATABASE_BASENAME:
            return -1
        if rhs == DATABASE_BASENAME:
            return 1
        return cmp(lhs, rhs)
    
    filenames.sort(cmp=name_cmp)
    return filenames


def cmd_anchor(target, update, **kwargs):
    dbpath = PATH.join(target, DATABASE_BASENAME)
    
    try:
        database = DB.Database(dbpath, autocreate=True)
        database.close()
    except ValueError, ex:
        print ex
        return
    except Exception, ex:
        print 'Unable to create anchor'
        print 'Error: %s' % (ex,)
        return
        
    if update:
        cmd_update([target], **kwargs)
        
    
def cmd_update(targets, quick=True, fset=None, skip_symlinks=False, skip_mounts=True, skip_devices=True, **kwargs):
    fskip_base = []
    fskip_path = []
    fskip_stats = []

    def fskip_base_mounts(parent, basename, userdata):
        if FS.is_mount(PATH.join(parent.truepath, basename)):
            return True
        return False
    
    def fskip_stats_rootfs(parent, path, stat, usertargets, userdata):
        if FS.is_lnk(stat):
            return False
        
        if FS.is_mount(path):
            if FS.is_sysmount(path):
                return True # skip system mounts
            userdata['root'] = path 
        elif 'root' in parent.userdata:
            userdata['root'] = parent.userdata['root']
        else:
            userdata['root'] = FS.rootpath(path)
            
        return False
    
    def fskip_stats_symlinks(parent, path, stat, usertargets, userdata):
        if FS.is_lnk(stat):
            return True
        return False
    
    def fskip_stats_devices(parent, path, stat, usertargets, userdata):
        if parent.stat.st_dev != stat.st_dev:
            return True
        return False

    if skip_mounts:
        fskip_base.append(fskip_base_mounts)

    if skip_symlinks:
        fskip_stats.append(fskip_stats_symlinks)

    if skip_devices:
        fskip_stats.append(fskip_stats_devices)
        
    fskip_stats.append(fskip_stats_rootfs)
        
    def compile(fskips):
        if len(fskips) == 0:
            return None
        def compiled(*args, **kwargs):
            return any(fskip(*args, **kwargs) for fskip in fskips)
        return compiled
    
    def fdoyield(target):
        return FS.is_reg(target.stat)
   
    # create a set of all databases
    databases = DB.Databases()
    for target in targets:
        target = FS.truepath(target)
        for path in FS.iterpath(target):
            filepath = PATH.join(path, DATABASE_BASENAME)
            if PATH.exists(filepath):
                 databases.push(FS.rootpath(path), filepath)

    # perform the walk
    for target in WALK.walk(targets, fdoyield=fdoyield, fskip_base=compile(fskip_base), fskip_path=compile(fskip_path), fskip_stats=compile(fskip_stats)):
        root = target.userdata.get('root')
        if root == None:
            root = FS.rootpath(target.truepath)
        
        if PATH.basename(target.truepath) == '.hashdb':
            databases.push(root, target.truepath)
                
        #print '[user]', target.usertargets[0].userpath
        #print root
        
        info = databases.file_get(root, target.truepath, time=target.stat.st_mtime, size=target.stat.st_size)
        data = None

        if ((info == None) and (fset == None) and (not databases.is_child(root, target.truepath))):
            print '[skip]', target.truepath
        elif (info == None)\
        or (info.hash_quick == None)\
        or ((info.hash_total == None) and (quick == False))\
        or (info.size != target.stat.st_size)\
        or (info.time != target.stat.st_mtime):
            print '[hash]', target.truepath
            filehash = HASH.hash(target.truepath, target.stat.st_size, quick)
            
            if filehash != None:
                data = {
                    'root' : root,
                    'path' : target.truepath,
                    'size' : target.stat.st_size,
                    'time' : target.stat.st_mtime,
                    'hash_quick' : filehash.hash_quick,
                    'hash_total' : filehash.hash_total
                }
        else:
            print '[keep]', target.truepath
            data = {
                'root' : root,
                'path' : info.path,
                'size' : info.size,
                'time' : info.time,
                'hash_quick' : info.hash_quick,
                'hash_total' : info.hash_total
            }
        
        if data != None:
            result = databases.file_set(**data)
            if fset != None:
                fset(target, data, result)
            
    for target in targets:
        path = FS.truepath(target)
        root = FS.rootpath(path)
        databases.purge(root, path)
    
    databases.commit()
    return databases


def cmd_export(targets, database, **kwargs):
    try:
        if PATH.exists(database):
            print 'target (%s)already exists' % database
        db_all = DB.Database(database, autocreate=True)
    except ValueError, ex:
        print ex
        return
    except Exception, ex:
        print 'Unable to create export database'
        print 'Error: %s' % (ex,)
        return
    
    def set(target, data, result):
        for usertarget in target.usertargets:
            db_all.file_set(
                path = usertarget.abspath,
                size = data['size'],
                time = data['time'],
                hash_quick = data['hash_quick'],
                hash_total = data['hash_total']
            )

    cmd_update(targets, fset=set, **kwargs)
    db_all.commit()
    db_all.close()
    
def cmd_compare(targets, database, **kwargs):
    db_all = DB.Database(':memory:', autocreate=True)
    
    def set(target, data, result):
        database.file_set(
            path = data['path'],
            size = data['size'],
            time = data['time'],
            hash_quick = data['hash_quick'],
            hash_total = data['hash_total']
        )

    db_all = cmd_update(targets, fset=set, **kwargs)

    db_all.commit()
    
    # database is a complete hash table, we can now just need to combine (do a db attach) with the target database and search for duplicates
    
    db_all.close()
    
def cmd_duplicates(targets, targets1, targets2, exact_match, **kwargs):
    print (targets, targets1, targets2)
    db_all = DBD.DuplicatesDatabase()
    
    targets1_abs = [PATH.abspath(t).split(PATH.sep) for t in targets1]
    targets2_abs = [PATH.abspath(t).split(PATH.sep) for t in targets2]
    
    def set(target, data, result):
        primary_paths = []
        secondary_paths = []
        for user in target.usertargets:
            parts = user.abspath.split(PATH.sep)
            for t in targets1_abs:
                if parts[:len(t)] == t:
                    primary_paths.append(user.abspath)
            for t in targets2_abs:
                if parts[:len(t)] == t:
                    secondary_paths.append(user.abspath)
        
        db_all.file_set(
            path = data['path'],
            stat = target.stat,
            primary_paths = primary_paths,
            secondary_paths = secondary_paths,
            size = data['size'],
            time = data['time'],
            hash_quick = data['hash_quick'],
            hash_total = data['hash_total']
        )

    databases = cmd_update(targets + targets1 + targets2, fset=set, **kwargs)
    
    db_all.compile_quick()
    for row in db_all.iterquick():
        print '[HASH]', row['path']
        hash = HASH.hash(row['path'], row['size'], quick=False)
        if hash != None:
            data = dict(**row)
            data.pop('is_primary', None)
            data.pop('is_secondary', None)
            data.update(hash._asdict())
            databases.file_set(FS.rootpath(row['path']), **data)
            db_all.file_update(**data)
            
    databases.commit()
    
    db_all.compile_total()
    
    for group in db_all.itertotal():
        for i,prefix in enumerate(['1:', '2:', '?:']):
            for r in group[i]:
                print prefix, r['path']
        print
        
    db_all.close()
