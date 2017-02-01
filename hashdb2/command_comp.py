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
    # ToDo: Work out creating Views and sort out schema names (attached db is in one schema, the other tables are in the main schema)
    # I *should* be able to have cross-database views

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

            attach(engine, ro)
            engine.execute(CreateView(ro, sel))

            pass
        elif subpath:
            # db = actual database
            # rw = LHSPATH restricted copy of lhsdb
            # ro = view of lhsrw
            pass
        else:
            # db = actual database
            # rw = copy of lhsdb
            # ro = view of lhsrw
            pass
    else:
        # rw = fresh memory database
        # ro = view f lhsrw
        pass

def command_comp(arguments):
    engine = create(None)
    with engine_dispose(engine):
        attach_side(engine, 'lhs', arguments['--lhs-db'], arguments['--lhs-update'], arguments['--lhs-path'])
        attach_side(engine, 'rhs', arguments['--rhs-db'], arguments['--rhs-update'], arguments['--rhs-path'])

