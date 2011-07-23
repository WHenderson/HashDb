import hashdb_sql as SQL
import sqlite3 as SQLITE
from collections import namedtuple
import time as TIME
import os.path as PATH

DBDetail = namedtuple('DBDetail', 'name path root tagid readonly count') # root is used to seperate file systems, count is for push/pop counting

COMMIT_CHANGE_THRESHOLD = 1000
COMMIT_TIME_THRESHOLD = 10.0

class Database(object):
    def __init__(self, keep_orphans=False):
        super(Database, self).__init__()
        
        self._commit_total_changes = 0
        self._commit_time = TIME.time()
        self._stack = {}
        self._connection = SQLITE.connect(':memory:')
        self._connection.row_factory = SQLITE.Row
        self._cursor = self._connection.cursor()
        self._dbmain = DBDetail(
            name='main',
            path=(),
            root=(),
            tagid=None,
            readonly=keep_orphans,
            count=1
        )
        self._connection.create_function(
            'PATHJOIN',
            2,
            SQL.func_pathjoin
        )
        self._connection.create_function(
            'PATHPREFIXED',
            2,
            SQL.func_pathprefixed
        )
        Database._sql_schema_create(self._connection, self._dbmain.name)
        
    def _smart_commit(self):
        if (self._connection.total_changes - self._commit_total_changes > COMMIT_CHANGE_THRESHOLD)\
        or (TIME.time() - self._commit_time > COMMIT_TIME_THRESHOLD):
            self.commit()
            
    @staticmethod
    def touch(path):
        with SQLITE.connect(path) as connection:
            Database._sql_schema_create(connection, 'main')
        
    @staticmethod
    def _sql_schema_create(connection, dbname):
        connection.executescript(SQL.SCHEMA_CREATE(dbname))
        connection.commit()
    
    @staticmethod
    def _sql_database_attach(connection, dbname, path):
        connection.execute(SQL.DATABASE_ATTACH(dbname), { 'path': path } )
        connection.commit()
        
    @staticmethod
    def _sql_database_detach(conn, dbname):
        connection.execute(SQL.DATABASE_DETACH(dbname))
        connection.commit()
    
    @staticmethod
    def _sql_data_pull(connection, dbfrom, dbto):
        return
        connection.execute(
            SQL.DATA_PULL(dbfrom.name, dbto.name),
            {
                'from_path':PATH.join(*dbfrom.path),
                'to_path':PATH.join(*dbto.path)
            }
        )
        connection.commit()
        
    @staticmethod
    def _sql_file_set(cursor, dbdetail, filerow):
        path = tuple(filerow.path.split(PATH.sep))
        #print 'set?'
        #print ' %s' % dbdetail.name
        #print ' %r' % (dbdetail.path,)
        #print ' %r' % (path,)
        #print ' %r' % (filerow.path,)
        if path[:len(dbdetail.path)] != dbdetail.path:
            #print 'skp!'
            return False
        path = path[len(dbdetail.path):]

        #print 'set!'
        
        filerow = filerow._replace(
            path = '/'.join(path),
            tagid = dbdetail.tagid
        )
        
        cursor.execute(
            SQL.FILE_SET(dbdetail.name),
            filerow._asdict()
        )
        
        return True
        
    @staticmethod
    def _sql_file_get(cursor, dbdetail, path):
        path = tuple(path.split(PATH.sep))
        if path[:len(dbdetail.path)] != dbdetail.path:
            return None
        path = '/'.join(path[len(dbdetail.path):])
        
        result = cursor.execute(
            SQL.FILE_GET(dbdetail.name),
            {
                'path':path
            }
        ).fetchone()
        if result == None:
            return None
        
        result = SQL.FileRow(**result) # this may not be correct, need to convert SQLITE.Row type to FileRow
        result = result._replace(
            path = PATH.sep.join(dbdetail.path + tuple(result.path.split('/')))  # PATH.join(*(dbdetail.path + tuple(result.path.split('/'))))
        )
        
        return result

    @staticmethod
    def _sql_files_purge(cursor, dbdetail, path):
        path = tuple(path.split(PATH.sep))
        if path[:len(dbdetail.path)] != dbdetail.path:
            return None
        path = '/'.join(path[len(dbdetail.path):])
        
        cursor.execute(
            SQL.FILES_PURGE(dbdetail.name),
            {
                'path':path,
                'tagid':dbdetail.tagid
            }
        )
    
    @staticmethod
    def _sql_tag_create(connection, dbname):
        connection.execute(
            SQL.TAG_CREATE(dbname)
        )
        result = connection.execute(
            SQL.TAG_LARGEST(dbname)
        ).fetchone()
        if result == None:
            return 0
        return result['tagid']
    
    def push(self, path, root):
        # Create the database details tuple
        dbdetail  = DBDetail(
            name  = 'db%02d' % (len(self._stack),),
            path  = tuple(PATH.dirname(path).split(PATH.sep)),
            root  = tuple(root.split(PATH.sep)),
            tagid = 0,
            readonly = True,
            count = 1
        )
        
        # already referenced?
        if dbdetail.path in self._stack:
            dbdetail = self._stack[dbdetail.path]
            self._stack[dbdetail.path] = self._stack[dbdetail.path]._replace(count=dbdetail.count + 1)
            return True
        
        # attach the database
        Database._sql_database_attach(self._connection, dbdetail.name, path)
        
        # create the schema (if it doesnt already exist)
        Database._sql_schema_create(self._connection, dbdetail.name)
        
        # create a new tagid, or 0 if it is readonly
        tagid = Database._sql_tag_create(self._connection, dbdetail.name)
        dbdetail = dbdetail._replace(
            tagid=tagid,
            readonly=(tagid == 0)
        )
        
        
        # pull values into new database
        dbdetail_root = None
        for dbdetail_ in self._stack.itervalues():
            if dbdetail_.root != dbdetail.root:
                continue
            if dbdetail_.path != dbdetail.path[:len(dbdetail_.path)]:
                continue
            if (dbdetail_root == None) or (len(dbdetail_.path) < len(dbdetail_root.path)):
                dbdetail_root = dbdetail_
        if dbdetail_root != None:
            Database._sql_data_pull(self._connection, dbfrom=dbdetail_root, dbto=dbdetail)    
        
        # push values into old databases
        for dbdetail_ in self._stack.itervalues():
            if dbdetail_.root != dbdetail.root:
                continue
            Database._sql_data_pull(self._connection, dbfrom=dbdetail, dbto=dbdetail_)    
        
        # put in the stack
        self._stack[dbdetail.path] = dbdetail
        
    def set_file(self, root, path, time, size, hash_start=None, hash_end=None, hash_total=None):
        # Set the file attributes and propegate them to all relevent db's
        root = tuple(root.split(PATH.sep))
        filerow = SQL.FileRow(
            path = path,
            size = size,
            time = time,
            hash_start = hash_start,
            hash_end = hash_end,
            hash_total = hash_total,
            tagid = None
        )
        
        # set file data in all (relevent) attached databases, or the main database if none are available
        stored = False
        for dbdetail in self._stack.itervalues():
            if dbdetail.readonly:
                continue
            if dbdetail.root != root:
                continue
            if Database._sql_file_set(self._cursor, dbdetail, filerow):
                stored = True
        
        if (stored == False) and (not self._dbmain.readonly):
            Database._sql_file_set(self._cursor, self._dbmain, filerow)
            
        self._smart_commit()
            
    def get_file(self, root, path, time=None, size=None):
        # Get a list of all file info available
        root = tuple(root.split(PATH.sep))
        
        results = set()
        for dbdetail in [db for db in self._stack.itervalues() if db.root == root] + [self._dbmain]:
            filerow = Database._sql_file_get(self._cursor, dbdetail, path)
            if filerow == None:
                continue
            if (time != None) and (filerow.time != time):
                continue
            if (size != None) and (filerow.size != size):
                continue
            results.add(filerow)
                
        if len(results) == 0:
            return None
        
        filerows = list(results)                
        filerows.sort(key=lambda filerow: (filerow.time, filerow.hash_total == None, filerow.hash_start == None, filerow.hash_end == None, filerow.size))
        
        result = filerows[0]
        for filerow in filerows[1:]:
            if (filerow != result.time) or (filerow.size != result.size):
                break
            result = result._replace(
                hash_start = result.hash_start if (result.hash_start != None) else filerow.hash_start,
                hash_end = result.hash_end if (result.hash_end != None) else filerow.hash_end,
                hash_total = result.hash_total if (result.hash_total != None) else filerow.hash_total
            )
        
        return result
            
    def commit(self):
        self._connection.commit()
        self._commit_total_changes = self._connection.total_changes
        self._commit_time = TIME.time()

    def purge(self, path):
        for dbdetail in self._stack.itervalues():
            Database._sql_files_purge(self._cursor, dbdetail, path)
        self._smart_commit()
