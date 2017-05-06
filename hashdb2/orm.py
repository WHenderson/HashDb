from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, ForeignKey
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement
from contextlib import contextmanager

def create(filename, echo=False):
    if filename is None:
        return create_engine('sqlite://', echo=echo)
    else:
        return create_engine('sqlite:///%s' % (filename,), echo=echo)

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
