from collections import namedtuple


FileData = namedtuple(
    'FileData',
    'path size time hash_quick hash_total tagid'
)

VERSION_MAJOR = 2
VERSION_MINOR = 1
VERSION_FIXES = 0
VERSION_BUILD = 1
VERSION_STATE = 'beta'

Version = namedtuple('Version', 'major minor fixes build state')

VERSION = Version(VERSION_MAJOR, VERSION_MINOR, VERSION_FIXES, VERSION_BUILD, VERSION_STATE)
VERSION_STRING = '%s.%s.%s.%s%s' % VERSION

SCHEMA_CREATE = """
    CREATE TABLE IF NOT EXISTS files(
        path PRIMARY KEY ASC,
        size,
        time,
        hash_quick,
        hash_total,
        tagid
    );
    
    CREATE TABLE IF NOT EXISTS tags(
        tagid INTEGER PRIMARY KEY ASC AUTOINCREMENT,
        time DEFAULT (DATETIME('now'))
    );
    
    CREATE TABLE IF NOT EXISTS metadata(
        key PRIMARY KEY ASC,
        data
    );
    
    INSERT OR IGNORE INTO metadata (key, data) VALUES (
        'version',
        '%(version)s'
    );
    """ % { 'version': VERSION_STRING }

SCHEMA_METADATA = """
    SELECT * FROM metadata WHERE key=:key
    """
    
FILE_GET = lambda filedata : """
    SELECT
        *
    FROM
        files
    WHERE
        %s
    """ % ' AND '.join(('%s=:%s' % (name, name)) for name in filedata.iterkeys())

FILE_SET  = lambda filedata: """
    INSERT OR REPLACE INTO files (%(names)s) VALUES(%(values)s)
    """ % { 'names': ','.join(name for name in filedata.iterkeys()), 'values': ','.join((':' + name) for name in filedata.iterkeys())}
    
FILES_PURGE = """
    DELETE FROM
        files
    WHERE
        (tagid <> :tagid) AND
        (
            (LENGTH(:path) = 0) OR
            (path = :path) OR
            (SUBSTR(path,LENGTH(:path) + 1) == :path || '/')
        )
    """
    
TAG_CREATE = """
    INSERT INTO tags DEFAULT VALUES;
    """
    
TAG_LARGEST = """
    SELECT * FROM tags WHERE tagid=(SELECT MAX(tagid) FROM tags)
    """
