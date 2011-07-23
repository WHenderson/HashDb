import sqlite3 as SQLITE
import re as RE
import os.path as PATH
import time as TIME
from collections import namedtuple

import hashdb_sql as SQL

COMMIT_CHANGE_THRESHOLD = 1000
COMMIT_TIME_THRESHOLD = 10.0

class Database(object):
    def __init__(self, filepath, autocreate=True):
        try:
            super(Database, self).__init__()
            
            self._commit_total_changes = 0
            self._commit_time = TIME.time()
    
            self._connection = SQLITE.connect(filepath)
            self._connection.row_factory = SQLITE.Row
            self._connection.text_factory = str
            self._cursor = self._connection.cursor()
            
            self._tagid = None
            self._readonly = True
            
            self._filepath  = filepath
            
            if filepath != ':memory:':
                self._filedir   = PATH.dirname(filepath)
                self._pathparts = self._filepath.split(PATH.sep)
                self._dirparts  = self._filedir.split(PATH.sep)
                if len(self._dirparts) > 1 and self._dirparts[-1] == '':
                    self._dirparts = self._dirparts[:-1]
            else:
                self._filedir   = ''
                self._pathparts = ['', filepath]
                self._dirparts  = ['']
            
            self._version = self._sql_version()
            if self._version == None:
                if autocreate:
                    self._sql_schema_create()
                    self._version = self._sql_version()
                    if self._version == None:
                        raise ValueError('unable to load file')
                else:
                    raise ValueError('unable to load file')
            if self._version != SQL.VERSION:
                raise ValueError('invalid file version')
                
            self._tagid = self._sql_tag_create()
        except SQLITE.OperationalError:
            raise ValueError('unable to load file')
        
    @property
    def readonly(self):
        return (self._tagid == None)
        
    def _sql_version(self):
        try:
            row = self._cursor.execute(
                SQL.SCHEMA_METADATA,
                {
                    'key':'version'
                }
            ).fetchone()
        except SQLITE.OperationalError:
            return None
            
        if (row == None) or ('data' not in row.keys()):
            return None
        else:
            try:
                info = RE.match(r'^(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<fixes>[0-9]+)\.(?P<build>[0-9]+)(?P<state>.*)$', row['data']).groupdict()
                return SQL.Version(int(info['major']), int(info['minor']), int(info['fixes']), int(info['build']), info['state'])
            except Exception, ex:
                print type(ex), ex
                return None
            
    def _sql_file_get(self, path, **filedata):
        filedata['path'] = self._path_internalize(path)
        if filedata['path'] == None:
            return None

        row = self._cursor.execute(
            SQL.FILE_GET(filedata),
            filedata
        ).fetchone()
        if row != None:
            row = SQL.FileData(**row)._replace(path=path)
        return row
        
    def _sql_file_set(self, path, **filedata):
        filedata['path'] = self._path_internalize(path)
        if filedata['path'] == None:
            return False
        filedata['tagid'] = self._tagid
        self._cursor.execute(
            SQL.FILE_SET(filedata),
            filedata
        )
        return True
        
    def _sql_purge(self, path):
        path = self._path_internalize(path)
        if path == None:
            path = ''
        
        self._cursor.execute(
            SQL.FILES_PURGE,
            {
                'tagid':self._tagid,
                'path':path
            }
        )
        
    def _sql_tag_create(self):
        try:
            self._cursor.execute(
                SQL.TAG_CREATE
            )
            result = self._connection.execute(
                SQL.TAG_LARGEST
            ).fetchone()
            if result == None:
                return None
            self.commit()
            return result['tagid']
        except SQLITE.OperationalError:
            return None
        
    def _sql_schema_create(self):
        self._cursor.executescript(SQL.SCHEMA_CREATE)
        self.commit()
        
    def _path_internalize(self, path):
        path = path.split(PATH.sep)
        if path[:len(self._dirparts)] != self._dirparts:
            return None
        return '/'.join(path[len(self._dirparts):])
        
    def _path_externalize(self, path):
        return PATH.sep.join(self._dirparts + path.split('/'))
        
    def _commit_smart(self):
        if (self._connection.total_changes - self._commit_total_changes > COMMIT_CHANGE_THRESHOLD)\
        or (TIME.time() - self._commit_time > COMMIT_TIME_THRESHOLD):
            self.commit()
        
    def is_child(self, path):
        path = path.split(PATH.sep)
        return path[:len(self._dirparts)] == self._dirparts
        
    def close(self, commit=True):
        if commit:
            self.commit()
        self._connection.close()
        
    def commit(self):
        self._connection.commit()
        self._commit_total_changes = self._connection.total_changes
        self._commit_time = TIME.time()
        
    def purge(self, path, vacuum=None):
        pathparts = path.split(PATH.sep)
        if self._dirparts[:len(pathparts)] == pathparts[:len(self._dirparts)]:
            self._sql_purge(path)
            self._commit_smart()
            if vacuum or ((vacuum == None) and (self._tagid % 100 == 0)):
                self.commit()
                self._cursor.execute('VACUUM')
    
    def file_set(self, path, **filedata):
        if self._sql_file_set(path, **filedata):
           self._commit_smart()
           return True
        return False
    
    def file_get(self, path, **filedata):
        return self._sql_file_get(path, **filedata)

    def create_index(self):
        self._sql_schema_index_create()
                    

DBInfo = namedtuple('DBInfo', 'root database')
    
class Databases(object):
    def __init__(self):
        super(Databases, self).__init__()
        
        self._stack = []
    
    def _stack_by_root(self, root):
        root = root.split(PATH.sep)
        for dbinfo in self._stack:
            if dbinfo.root == root:
                yield dbinfo
    
    def push(self, root, database):
        if not isinstance(database, Database):
            for dbinfo in self._stack:
                if dbinfo.database._filepath == database:
                    return True
            try:
                database = Database(filepath=database, autocreate=False)
            except:
                return False
        
        self._stack.append(DBInfo(
            root = root.split(PATH.sep),
            database = database
        ))
        return True
        
    def is_child(self, root, path, rw=False):
        for dbinfo in self._stack_by_root(root):
            if rw and dbinfo.database.readonly:
                continue
            if dbinfo.database.is_child(path):
                return True
        return False
    
    def close(self):
        while self._stack:
            self._stack.pop().database.close()
    
    def commit(self):
        for dbinfo in self._stack:
            if dbinfo.database.readonly:
                continue
            dbinfo.database.commit()
            
    def purge(self, root, path, vacuum=None):
        for dbinfo in self._stack_by_root(root):
            if dbinfo.database.readonly:
                continue
            dbinfo.database.purge(path, vacuum=vacuum)
            
    def file_set(self, root, path, **filedata):
        result = False
        for dbinfo in self._stack_by_root(root):
            if dbinfo.database.readonly:
                continue
            if dbinfo.database.file_set(path, **filedata):
                result = True
        return result
    
    def file_get(self, root, path, **kwargs):
        results = []
        for dbinfo in self._stack_by_root(root):
            filedata = dbinfo.database.file_get(path, **kwargs)
            if filedata != None:
                results.append(filedata)

        if len(results) == 0:
            return None
        
        results.sort(key=lambda filedata: (filedata.time, filedata.size, filedata.hash_total == None, filedata.hash_quick == None))
        result = results[0]
        for filedata in results[1:]:
            if (filedata.time != result.time) or (filedata.size != result.size):
                break
            result = result._replace(
                hash_quick = result.hash_quick if (result.hash_quick != None) else filedata.hash_quick,
                hash_total = result.hash_total if (result.hash_total != None) else filedata.hash_total
            )
        
        return result
        