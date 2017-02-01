from .orm import create, attach, create_schema, touch, CreateView, engine_dispose
from .command_hash import command_hash
from sqlalchemy import MetaData, Table, and_, or_, func, select
import os.path

def is_subpath(column, subpath):
    subpathdir = subpath
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

            if subpath and exists:
                # rw = actual database
                # ro = view of lhsrw, restricted to LHSPATH
                sel = sel.where(is_subpath(rwFiles.c.path, subpath))
            else:
                # rw = actual database, created from scratch if necessary
                # ro = view of lhsrw
                pass

            if subpath:
                command_hash({'INPUTS': [subpath], '--quick': False, '--full': False, '--none': True }, engine=engine, schema=rw)

            engine.execute(CreateView(ro, sel))
            roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)

            return rwFiles, roFiles
        else:
            attach(engine, db, dbpath)
            dbFiles = Table('Files', MetaData(schema=db), autoload=True, autoload_with=engine)

            sel = dbFiles.select()

            if subpath:
                # db = actual database
                # rw = None
                # ro = LHSPATH restricted view of lhsdb
                sel = sel.where(is_subpath(dbFiles.c.path, subpath))
            else:
                # db = actual database
                # rw = None
                # ro = view of lhsdb
                pass

            engine.execute(CreateView(ro, sel))
            roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)

            return None, roFiles
    else:
        # rw = fresh memory database
        # ro = view f lhsrw

        attach(engine, rw)
        create_schema(engine, rw)
        rwFiles = Table('Files', MetaData(schema=rw), autoload=True, autoload_with=engine)

        engine.execute(CreateView(ro, rwFiles.select()))
        roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)

        if subpath:
            command_hash({'INPUTS': [subpath], '--quick': False, '--full': False, '--none': True}, engine=engine, schema=rw)

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

        if not (lhsrwFiles is None and rhsrwFiles is None) and not arguments['--none']:
            # Do a preliminary comparison

            def match(sel):
                if arguments['--size']:
                    sel = sel.where(lhsroFiles.c.size == rhsroFiles.c.size)

                if arguments['--time']:
                    sel = sel.where(lhsroFiles.c.time == rhsroFiles.c.time)

                if arguments['--extension']:
                    sel = sel.where(lhsroFiles.c.extension == rhsroFiles.c.extension)

                if arguments['--basename']:
                    sel = sel.where(lhsroFiles.c.basename == rhsroFiles.c.basename)

                return sel

            lhssel = match(select([lhsroFiles.c.path]))
            rhssel = match(select([rhsroFiles.c.path]))

            # Update rw table
            conn = engine.connect()
            try:
                for result in conn.execute(lhssel):
                    # ToDo: Update hash for lhsrw
                    pass
                for result in conn.execute(rhssel):
                    # ToDo: Update hash for rhsrw
                    pass
            finally:
                conn.close()

        # Do the full comparison

