from peewee import *
import sqlite3

def create_schema(conn=None, schemaName='main'):
    if conn is None:
        conn = sqlite3.connect(':memory:')
    elif isinstance(conn, str):
        conn = sqlite3.connect(conn)

    sql = '''
    CREATE TABLE IF NOT EXISTS "%(schemaName)s"."Files" (
      "path" TEXT NOT NULL PRIMARY KEY,
      "basename" TEXT NOT NULL,
      "extension" TEXT NOT NULL,

      "size" INTEGER NOT NULL,
      "time" REAL NOT NULL,
      "hash_quick" CHAR(32),
      "hash_total" CHAR(32)
    )
    ''' % { 'schemaName': schemaName }

    conn.execute(sql)
