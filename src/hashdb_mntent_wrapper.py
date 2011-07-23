#!/usr/bin/python

try:
    from hashdb_mntent import mntent, setmntent, getmntent_r, endmntent
    import ctypes
except:
    setmntent = lambda filename: None

import os as OS
import os.path as PATH
from collections import namedtuple

import hashdb_path as PATHPARTS

MountEntry = namedtuple('MountEntry', 'fsname dir type opts freq passno')

def enum_mntent(filename):
    stream = setmntent(filename)
    if not stream:
        return []

    try:
        buf    = ctypes.create_string_buffer(4095)
        mount  = mntent()
        results = []
        while getmntent_r(stream, mount, ctypes.byref(buf), ctypes.sizeof(buf) - 1):
            results.append(MountEntry(
                mount.mnt_fsname,
                mount.mnt_dir,
                mount.mnt_type,
                set(mount.mnt_opts.split(',')),
                mount.mnt_freq,
                mount.mnt_passno,
            ))
        return results
    finally:
        endmntent(stream)

class MountEntries(object):
    def __init__(self, filenames=['/etc/mtab', '/proc/mounts']):
        super(MountEntries, self).__init__()

        self._entries_by_fn   = {} # 
        self._entries_by_root = {}
        self._entries_by_root_nobinds = {}
        self._types_by_root = {}
        self._binds = {}
        
        for filename in filenames:
            try:
                self._entries_by_fn[filename] = list(enum_mntent(filename))
            except IOError:
                continue
            except OSError:
                continue
        
            for entry in self._entries_by_fn[filename]:
                root = PATHPARTS.path_2_tuple(entry.dir)
                self._entries_by_root.setdefault(root, []).append(entry)
                if (entry.type != 'none') or ('bind' not in entry.opts):
                    self._entries_by_root_nobinds.setdefault(root, []).append(entry)
                    self._types_by_root.setdefault(root, set()).add(entry.type)

        def resolve_bind(root, depth=255):
            if depth == 0:
                return None
            
            parts = ()
            for node in root:
                parts = parts + (node,)
                for entry in self._entries_by_root.get(parts, []):
                    if (entry.type == 'none') and ('bind' in entry.opts):
                        input = parts
                        parts = resolve_bind(PATHPARTS.path_2_tuple(entry.fsname), depth - 1)
                        if parts == None:
                            return None
                        else:
                            break
            return parts
                
        for root in self._entries_by_root.keys():
            source = resolve_bind(root)
            if (source != None) and (source != root):
                self._binds[root] = source

    def is_mount(self, truepath):
        ''' Returns true for any kind of mount, even bind mounts '''
        return PATHPARTS.path_2_tuple(truepath) in self._entries_by_root
        
    def is_bindmount(self, truepath):
        ''' Returns true if this is a bind mount'''
        return PATHPARTS.path_2_tuple(truepath) in self._binds
    
    def is_sysmount(self, truepath):
        truepath = self.truepath(truepath)
        return len(self._types_by_root.get(PATHPARTS.path_2_tuple(truepath), set()).intersection([
            'sysfs',
            'proc',
            'devtmpfs',
            'devpts',
            'fusectl',
            'debugfs',
            'securityfs',
            'tmpfs',
            'binfmt_misc'
        ])) != 0
        
    def truepath(self, path):
        try:
            path = PATH.realpath(path)
            parts = PATHPARTS.path_2_tuple(path)
            for x in range(len(parts), 0, -1):
                part = parts[:x]
                if part in self._binds:
                    parts = self._binds[part] + parts[x:]
                    path = PATHPARTS.path_2_string(parts)
                    return path
            return path
        except OSError, ex:
            return None
        except RuntimeError, ex:
            # found that two symlinks as described below cause inf recursion in python 2.6
            # a -> b/b1/linkto_a
            # b -> a/a1/linkto_b
            return None
        
    def rootpath(self, truepath, binds=True):
        truepath = PATHPARTS.path_2_tuple(truepath)
        if binds:
            entries = self._entries_by_root
        else:
            entries = self._entries_by_root_nobinds
        for x in range(len(truepath), 1, -1):
            parts = truepath[:x]
            if parts in entries:
                return PATHPARTS.path_2_string(parts)
        return PATHPARTS.path_2_string(truepath[:1])
        
    def __str__(self):
        lines = []
        for filename, entries in self._entries_by_fn.iteritems():
            lines.append('; %s' % filename)
            lines.extend(('%s' % (entry,)) for entry in entries)
        
        lines.append('; bind mappings')
        roots = self._binds.keys()
        roots.sort()
        for root in roots:
            lines.append('%s => %s' % (PATH.sep.join(root), PATH.sep.join(self._binds[root])))
        
        return '\n'.join(lines)

if __name__ == '__main__':
    mounts = MountEntries()
    print mounts

    import sys as SYS
    for path in SYS.argv[1:]:
        realpath = PATH.realpath(path)
        print '[%s]' % path
        print 'truepath :', mounts.truepath(realpath)
        print 'is_mount :', mounts.is_mount(realpath)