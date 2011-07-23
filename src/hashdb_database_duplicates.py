import sqlite3 as SQLITE
import re as RE
import os as OS
import os.path as PATH
import time as TIME
from collections import namedtuple

import hashdb_sql_duplicates as SQL
import hashdb_fs as FS
from hashdb_walk import TrueTarget, UserTarget

class DuplicatesDatabase(object):
    def __init__(self):
        super(DuplicatesDatabase, self).__init__()
        
        dbname = ':memory:'
        dbname = 'test.db'

        try:
            OS.remove(dbname)
        except Exception, ex:
            print type(ex), ex
        
        self._connection = SQLITE.connect(dbname) # will be changed to ':memory:' once its working
        self._connection.row_factory = SQLITE.Row
        self._connection.text_factory = str
        if dbname == ':memory:':
            self._connection.isolation_level = None
        self._cursor = self._connection.cursor()
        
        self._cursor.executescript(SQL.SCHEMA_CREATE)
        self._connection.commit()

        
    def file_set(self, path, stat, primary_paths, secondary_paths, **filedata):
        # setup the primary/secondary tagging
        filedata['is_primary'] = (len(primary_paths) != 0)
        filedata['is_secondary'] = (len(secondary_paths) != 0)
        if not filedata['is_primary'] and not filedata['is_secondary']:
            filedata['is_primary'] = True
            filedata['is_secondary'] = True
       
                
        filedata['path'] = path # this is only a temporary database, no need to normalize the path

        self._cursor.execute(
            SQL.FILE_SET,
            filedata
        )
        
        for userpath in primary_paths:
            userdata = {
                'truepath':path,
                'userpath':userpath,
                'is_primary':True,
                'is_secondary':False
            }
            self._cursor.execute(
                SQL.USER_SET,
                userdata
            )
        for userpath in secondary_paths:
            userdata = {
                'truepath':path,
                'userpath':userpath,
                'is_primary':False,
                'is_secondary':True
            }
            self._cursor.execute(
                SQL.USER_SET,
                userdata
            )
            
    def file_update(self, path, is_primary=None, is_secondary=None, **filedata):
        filedata['path'] = path
        self._connection.execute(
            SQL.FILE_UPDATE(filedata),
            filedata
        )
            
    def compile_quick(self):
        self._cursor.execute(
            SQL.COMPILE_DUPLICATES_QUICK
        )
        self._connection.commit()
            
    def compile_total(self):
        self._cursor.execute(
            SQL.COMPILE_DUPLICATES_TOTAL
        )
        self._connection.commit()
        
    def iterquick(self):
        for row in self._cursor.execute(SQL.SELECT_DUPLICATES_QUICK):
            try:
                stat = OS.lstat(row['path'])
            except OSError:
                continue
            except IOError:
                continue
            
            yield row
            
        
    def itertotal(self):
        last = None
        for row in self._cursor.execute(SQL.SELECT_DUPLICATES_TOTAL):
            if ((last == None)
            or  (last['size'] != row['size'])
            or  (last['hash_total'] != row['hash_total'])):
                if last != None:
                    yield (a,b,c)
                last = row
                a = []
                b = []
                c = []
                
            if row['is_primary'] == 1 and row['is_secondary'] == 1:
                c.append(row)
            elif row['is_primary'] == 1:
                a.append(row)
            elif row['is_secondary'] == 1:
                b.append(row)
        if last != None:
            yield (a,b,c)
        
    def close(self):
        self._connection.commit()
        self._connection.close()
