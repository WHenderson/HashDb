from collections import namedtuple

FileData = namedtuple(
    'FileData',
    'path size time hash_quick hash_total is_primary is_secondary'
)
UserData = namedtuple(
    'UserData',
    'truepath userpath is_primary is_secondary'
)

SCHEMA_CREATE = """
    CREATE TABLE IF NOT EXISTS files(
        path PRIMARY KEY,
        size,
        time,
        hash_quick,
        hash_total DEFAULT NULL,
        is_primary   DEFAULT 0,
        is_secondary DEFAULT 0
    );
    
    CREATE TABLE IF NOT EXISTS userpaths(
        truepath PRIMARY KEY,
        userpath,
        is_primary   DEFAULT 0,
        is_secondary DEFAULT 0
    );
    
    --CREATE INDEX IF NOT EXISTS index_a ON files (is_primary, is_secondary, size, hash_quick, path);
    --CREATE INDEX IF NOT EXISTS index_b ON files (is_primary, is_secondary, size, hash_total, path);
    --CREATE TABLE IF NOT EXISTS duplicates_quick(
    --    size NOT NULL,
    --    hash NOT NULL
    --);
    --CREATE TABLE IF NOT EXISTS duplicates_total(
    --    size NOT NULL,
    --    hash NOT NULL
    --);
    --CREATE UNIQUE INDEX IF NOT EXISTS index_duplicates_quick ON duplicates_quick (size, hash);
    --CREATE UNIQUE INDEX IF NOT EXISTS index_duplicates_total ON duplicates_total (size, hash);
    """
    
FILE_SET  = """
    INSERT OR REPLACE INTO files (
        path,
        size,
        time,
        hash_quick,
        hash_total,
        is_primary,
        is_secondary
    ) VALUES (
        :path,
        :size,
        :time,
        :hash_quick,
        COALESCE(:hash_total, (SELECT hash_total FROM files WHERE path=:path)),
        :is_primary OR COALESCE((SELECT is_primary FROM files WHERE path=:path), 0),
        :is_secondary OR COALESCE((SELECT is_secondary FROM files WHERE path=:path), 0)
    )
    """

USER_SET = """
    INSERT OR REPLACE INTO userpaths (
        truepath,
        userpath,
        is_primary,
        is_secondary
    ) VALUES (
        :truepath,
        :userpath,
        :is_primary OR COALESCE((SELECT is_primary FROM userpaths WHERE truepath=:truepath), 0),
        :is_secondary OR COALESCE((SELECT is_secondary FROM userpaths WHERE truepath=:truepath), 0)
    )
    """

COMPILE_DUPLICATES_QUICK = """
    --CREATE INDEX IF NOT EXISTS idx_files_quick ON files (is_primary, is_secondary, size, hash_quick, path);
    
    CREATE TABLE IF NOT EXISTS
        quick
    AS
    SELECT DISTINCT
        a.size as size,
        a.hash_quick as hash
    FROM
        files a
    JOIN
        files b
    ON
        (a.is_primary = 1) AND
        (b.is_secondary = 1) AND
        (a.size = b.size) AND
        (a.hash_quick = b.hash_quick) AND
        (a.path <> b.path)
    ORDER BY
        a.path,
        b.path
    """
    
SELECT_DUPLICATES_QUICK = """
    --CREATE INDEX IF NOT EXISTS idx_files_quick_select ON files (size, hash_quick, hash_total, path, time);
    
    SELECT
        a.*
    FROM
        quick d
    JOIN
        files a
    ON
        d.size = a.size AND
        d.hash = a.hash_quick AND
        a.hash_total IS NULL
    ORDER BY
        d.size,
        d.hash,
        a.path,
        a.is_primary,
        a.is_secondary
    """

FILE_UPDATE = lambda filedata: """
    UPDATE files SET %(assign)s WHERE path=:path
    """ % { 'assign': ','.join((name + '=:' + name) for name in filedata.iterkeys() if name != 'path') }

COMPILE_DUPLICATES_TOTAL = """
    CREATE TABLE IF NOT EXISTS
        total
    AS
    SELECT DISTINCT
        a.size as size,
        a.hash_total as hash
    FROM
        files a
    JOIN
        files b
    ON
        (a.is_primary = 1) AND
        (b.is_secondary = 1) AND
        (a.size = b.size) AND
        (a.hash_total NOT NULL) AND
        (a.hash_total = b.hash_total)
    ORDER BY
        a.path,
        b.path
    """

SELECT_DUPLICATES_TOTAL = """
    SELECT
        a.*
    FROM
        total d
    JOIN
        files a
    ON
        d.size = a.size AND
        d.hash = a.hash_total
    --ORDER BY
    --    d.size,
    --    d.hash,
    --    a.path,
    --    a.is_primary,
    --    a.is_secondary
    """

# simple duplicates:
#   primary vs secondary. what to do about duplicate duplicates. ie, copy of file a is in primary twice, and secondary once. it will be reported twice...
#   select a.path, b.path from files a join files b on (a.size=b.size) and (a.hash_quick=b.hash_quick) and (a.is_primary=1 AND a.is_secondary=0) and (b.is_primary=0 AND b.is_secondary=1);
#
# simple duplicates with no ambiguity:
#   primary vs secondary, primary must be unique
#   select a.path, b.path from files a join files b on (a.size=b.size) and (a.hash_quick=b.hash_quick) and (a.is_primary=1 AND a.is_secondary=0) and (b.is_primary=0 AND b.is_secondary=1) where a.path in (select path from files where (is_primary=1 AND is_secondary=0) group by size, hash_quick having count(*)=1);

# f in primary once
# | f in primary multiple times
# | | f in secondary once
# | | | f in secondary multiple times
# | | | | f in ternary once
# | | | | | f in ternary multiple times
# | | | | | | result
# | | | | | | |
# x - - - - - : ignore
# - x - - - - : ignore
# x - x - - - : simple (1 : 1)
# - x x - - - : ambiguous! (* : 1)
# x - - x - - : simple (1 : *)
# - x - x - - : ambiguous! (* : *)
# x - - - x - : query? (1 : 1)
# - x - - x - : query? ambiguous! (* : 1)
# x - - - - x : 

