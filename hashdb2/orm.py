from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, ForeignKey
from contextlib import contextmanager
import sqlite3
from .filepath import gen_group_filepath, FilePath

def create(filename, echo=False, separator=None):
    def create_sqlite():
        conn = sqlite3.connect(filename) if filename != None else sqlite3.connect(':memory:')
        if separator != None:
            conn.create_aggregate('group_filepath', 1, gen_group_filepath(separator))
        return conn

    return create_engine('sqlite://', echo=echo, creator=create_sqlite)

def touch(filename):
    engine = create(filename)
    create_schema(engine)
    engine.dispose()

def attach(engine, name, filename=''):
    return engine.execute('ATTACH DATABASE ? AS ?', (filename, name))

def create_schema(engine, schema='main'):

    metadata = MetaData(schema=schema)
    Files = Table('Files', metadata,
        Column('path', String, primary_key=True, nullable=False),
        Column('name', String, nullable=False),
        Column('extension', String, nullable=False),

        Column('size', Integer, nullable=False),
        Column('time', Integer, nullable=False),

        Column('hash_quick', String(32), nullable=True),
        Column('hash_total', String(32), nullable=True)
    )
    metadata.create_all(engine)

    return engine

@contextmanager
def engine_dispose(engine):
    try:
        yield engine
    finally:
        engine.dispose()
