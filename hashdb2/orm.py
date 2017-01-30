from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, ForeignKey
#from collections import namedtuple

#File = namedtuple('File', ('path', 'basename', 'extension', 'size', 'time', 'hash_quick', 'hash_total'))

def create(filename=':memory:', echo=True):
    return create_engine('sqlite:///%s' % (filename,), echo=echo)

def attach(engine, name, filename=''):
    return engine.execute('ATTACH DATABASE ? AS ?', (filename, name))

def create_schema(engine, schema='main'):

    metadata = MetaData(schema=schema)
    Files = Table('Files', metadata,
        Column('path', String, primary_key=True, nullable=False),
        Column('name', String, nullable=False),
        Column('extension', String, nullable=False),

        Column('size', Integer, nullable=False),
        Column('time', Float, nullable=False),

        Column('hash_quick', String(32), nullable=True),
        Column('hash_total', String(32), nullable=True)
    )
    metadata.create_all(engine)

    return engine
