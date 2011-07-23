from collections import namedtuple

FileRow  = namedtuple('FileRow', 'path size time hash_start hash_end hash_total tagid')
TagRow   = namedtuple('TagRow', 'path dest')

SCHEMA_CREATE = lambda dbname : """
    CREATE TABLE IF NOT EXISTS %(dbname)s.tab_files(
        path PRIMARY KEY ASC,
        size,
        time,
        hash_start,
        hash_end,
        hash_total,
        tagid
    );
    
    CREATE TABLE IF NOT EXISTS %(dbname)s.tab_tags(
        tagid INTEGER PRIMARY KEY ASC AUTOINCREMENT,
        time DEFAULT (DATETIME('now'))
    );
    """ % { 'dbname': dbname }


DATABASE_ATTACH = lambda dbname : """
    ATTACH DATABASE :path AS %(dbname)s
    """ % { 'dbname': dbname }

DATABASE_DETACH = lambda dbname : """
    DETACH DATABASE %(dbname)s
    """ % { 'dbname': name }

DATA_PULL = lambda dbfrom, dbto : """
    -- update/replace existing
    INSERT OR REPLACE INTO %(to)s.tab_files VALUES (
        SELECT
            tab_to.path AS path,
            tab_from.size AS size,
            tab_from.time AS time,
            (CASE 
                WHEN (tab_from.time > tab_to.time) THEN tab_from.hash_start
                ELSE coalesce(tab_from.hash_start, tab_to.hash_start)
            END) AS hash_start,
            (CASE 
                WHEN (tab_from.time > tab_to.time) THEN tab_from.hash_end
                ELSE coalesce(tab_from.hash_end, tab_to.hash_end)
            END) AS hash_end,
            (CASE 
                WHEN (tab_from.time > tab_to.time) THEN tab_from.hash_total
                ELSE coalesce(tab_from.hash_total, tab_to.hash_total)
            END) AS hash_total,
            (CASE 
                WHEN (tab_from.time > tab_to.time) THEN 0
                ELSE tab_to.tagid
            END) AS tagid
        FROM
            %(to)s.tab_files AS tab_to
        FULL JOIN
            %(from)s.tab_files AS tab_from
        ON
            (PATHJOIN(:from_path, tab_from.path) = PATHJOIN(:to_path, tab_to.path)) AND
            (
                (tab_from.time > tab_to.time) OR
                (
                    (tab_from.time = tab_to.time) AND
                    (
                        ((tab_from.hash_start NOTNULL) AND (tab_from.hash_start <> tab_to.hash_start)) OR
                        ((tab_from.hash_end   NOTNULL) AND (tab_from.hash_end   <> tab_to.hash_end)) OR
                        ((tab_from.hash_total NOTNULL) AND (tab_from.hash_total <> tab_to.hash_total))
                    )
                )
            )
    );
    
    -- insert missing
    INSERT INTO %(to)s.tab_files VALUES (
        SELECT
            PATHPREFIXED(:to_path,PATHJOIN(:from_path, tab_from.path)) AS path,
            tab_from.size AS size,
            tab_from.time AS time,
            tab_from.hash_start AS hash_start,
            tab_from.hash_end AS hash_end,
            tab_from.hash_total AS hash_total,
            0 as tagid
        FROM
            %(from)s.tab_files AS from
        WHERE
            (PATHPREFIXED(:to_path,PATHJOIN(:from_path, tab_from.path)) NOT NULL) AND
            (
                NOT EXSITS(
                    SELECT
                        *
                    FROM
                        %(to)s.tab_file AS to
                    WHERE
                        (PATHJOIN(:from_path, tab_from.path) = PATHJOIN(:to_path, tab_to.path))
                )
            )
    );
    """ % { 'to':dbto, 'from':dbfrom }

FILE_SET  = lambda dbname: """
    INSERT OR REPLACE INTO %(dbname)s.tab_files (path, size, time, hash_start, hash_end, hash_total, tagid) VALUES(
        :path,
        :size,
        :time,
        :hash_start,
        :hash_end,
        :hash_total,
        :tagid
    )
    """ % { 'dbname':dbname }

FILE_GET  = lambda dbname : """
    SELECT
        *
    FROM
        %(dbname)s.tab_files
    WHERE
        path=:path
    """ % { 'dbname':dbname }

FILES_PURGE = lambda dbname : """
    DELETE FROM
        %(dbname)s.tab_files
    WHERE
        (
            (LENGTH(:path) = 0) OR
            (path = :path) OR
            (SUBSTR(path,LENGTH(:path) + 1) == :path || '/')
        ) AND
        (tagid <> :tagid)
    """ % { 'dbname':dbname }

TAG_CREATE = lambda dbname : """
    INSERT INTO %(dbname)s.tab_tags DEFAULT VALUES;
    """ % { 'dbname': dbname }
    
TAG_LARGEST = lambda dbname : """
    SELECT * FROM %(dbname)s.tab_tags WHERE tagid=(SELECT MAX(tagid) FROM %(dbname)s.tab_tags)
    """ % { 'dbname': dbname }
    
def func_pathjoin(lhs, rhs):
    return '/'.join((lhs, rhs))
    
def func_pathprefixed(prefix, path):
    prefix = prefix.split('/')
    path = path.split('/')
    if path[:len(prefix)] != prefix:
        return None
    return '/'.join(path[len(prefix):])
