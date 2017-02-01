from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, ForeignKey
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement
#from collections import namedtuple
from contextlib import contextmanager

#File = namedtuple('File', ('path', 'basename', 'extension', 'size', 'time', 'hash_quick', 'hash_total'))

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
    yield engine
    engine.dispose()
