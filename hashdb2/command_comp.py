from .orm import create, attach, create_schema, touch, CreateView, engine_dispose
from sqlalchemy import MetaData, Table, and_, or_, func
import os.path

def is_subpath(column, subpath):
    subpathdir = subpath = arguments['LHSPATH']
    if subpath.find('/') != -1:
        if not subpath.endswith('/'):
            subpathdir = subpath + '/'
    elif subpath.find('\\') != -1:
        if not subpath.endswith('\\'):
            subpathdir = subpath + '\\'

    if subpath != subpathdir:
        return or_(
            column == subpath,
            func.SUBSTR(column, 1, len(subpathdir)) == subpathdir
        )
    else:
        return func.SUBSTR(column, 1, len(subpathdir)) == subpathdir

def attach_side(engine, side, dbpath, update, subpath):
    db = side + 'db'
    rw = side + 'rw'
    ro = side + 'ro'

    if dbpath:
        exists = os.path.exists(dbpath)

        if update or not exists:

            if not exists:
                touch(dbpath)

            attach(engine, rw, dbpath)

            rwFiles = Table('Files', MetaData(schema=rw), autoload=True, autoload_with=engine)

            sel = rwFiles.select()

            if subpath:
                # rw = actual database, created from scratch if necesary
                # ro = view of lhsrw, restricted to LHSPATH
                sel = sel.where(is_subpath(rwFiles.c.path, subpath))
            else:
                # rw = actual database, created from scratch if necesary
                # ro = view of lhsrw
                pass

            engine.execute(CreateView(ro, sel))
            roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)

            return rwFiles, roFiles
        else:
            attach(engine, db, dbpath)
            dbFiles = Table('Files', MetaData(schema=db), autoload=True, autoload_with=engine)

            attach(engine, rw)
            create_schema(engine, rw)
            rwFiles = Table('Files', MetaData(schema=rw), autoload=True, autoload_with=engine)

            engine.execute(CreateView(ro, rwFiles.select()))
            roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)

            sel = dbFiles.select()

            if subpath:
                # db = actual database
                # rw = LHSPATH restricted copy of lhsdb
                # ro = view of lhsrw
                sel = sel.where(is_subpath(dbFiles.c.path, subpath))
            else:
                # db = actual database
                # rw = copy of lhsdb
                # ro = view of lhsrw
                pass

            rwFiles.insert().from_select(dbFiles.c.values(), sel)

            return rwFiles, roFiles
    else:
        # rw = fresh memory database
        # ro = view f lhsrw

        attach(engine, rw)
        create_schema(engine, rw)
        rwFiles = Table('Files', MetaData(schema=rw), autoload=True, autoload_with=engine)

        engine.execute(CreateView(ro, rwFiles.select()))
        roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)

        return rwFiles, roFiles


def command_comp(arguments):

    if not any(arguments[name] for name in ('--full', '--quick', '--none')):
        arguments['--none'] = True

    if not arguments['--none']:
        arguments['--size'] = True

    engine = create(None)
    with engine_dispose(engine):
        lhsrwFiles, lhsroFiles = attach_side(engine, 'lhs', arguments['--lhs-db'], arguments['--lhs-update'], arguments['--lhs-path'])
        rhsrwFiles, rhsroFiles = attach_side(engine, 'rhs', arguments['--rhs-db'], arguments['--rhs-update'], arguments['--rhs-path'])

