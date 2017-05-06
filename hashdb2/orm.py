from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, ForeignKey
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement
#from collections import namedtuple
from contextlib import contextmanager
import sqlite3

#File = namedtuple('File', ('path', 'basename', 'extension', 'size', 'time', 'hash_quick', 'hash_total'))

def create(filename, echo=False, readonly=False):
    if filename is None:
        return create_engine('sqlite://', echo=echo)
    elif not readonly:
        return create_engine('sqlite:///%s' % (filename,), echo=echo)
    else:
        return create_engine('sqlite:///', echo=echo, engine_kwargs={'creator': sqlite3.connect('file:' + db_file + '?mode=ro', uri=True)})

def touch(filename):
    engine = create(filename)
    print('sqlite version:', engine.pool._dialect.dbapi.sqlite_version_info)
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

class CreateView(Executable, ClauseElement):
    def __init__(self, name, select):
        self.name = name
        self.select = select

@compiles(CreateView, 'sqlite')
def visit_create_view(element, compiler, **kw):
    return "CREATE TEMPORARY VIEW IF NOT EXISTS %s AS %s" % (
         element.name,
         compiler.process(element.select, literal_binds=True)
     )

@contextmanager
def engine_dispose(engine):
    try:
        yield engine
    except Exception as ex:
        pass
    engine.dispose()
