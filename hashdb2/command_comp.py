from .orm import create, attach, create_schema, touch, CreateView, engine_dispose
from .command_hash import command_hash
from sqlalchemy import MetaData, Table, and_, or_, func, select, exists
import os.path
import re
from .hash import hashfile
from docopt import DocoptExit
from itertools import chain

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

    if arguments['--lhs-update'] and arguments['--lhs-path']:
        arguments['--lhs-path'] = os.path.realpath(arguments['--lhs-path'])

    if arguments['--rhs-update'] and arguments['--rhs-path']:
        arguments['--rhs-path'] = os.path.realpath(arguments['--rhs-path'])

    def match(sel, lhs, rhs, complete=False):
        if arguments['--size']:
            sel = sel.where(lhs.c.size == rhs.c.size)

        if arguments['--time']:
            sel = sel.where(lhs.c.time == rhs.c.time)

        if arguments['--extension']:
            sel = sel.where(lhs.c.extension == rhs.c.extension)

        if arguments['--basename']:
            sel = sel.where(lhs.c.basename == rhs.c.basename)

        if complete and arguments['--quick']:
            sel = sel.where(and_(
                lhs.c.hash_quick == rhs.c.hash_quick,
                lhs.c.hash_quick != None
            ))

        if complete and arguments['--full']:
            sel = sel.where(and_(
                lhs.c.hash_total == rhs.c.hash_total,
                lhs.c.hash_total != None
            ))

        # Not looking for the actual same file
        sel = sel.where(lhs.c.path != rhs.c.path)

        return sel

    def match_group(sel, lhs, rhs):
        group = []
        if arguments['--size']:
            group.append(lhs.c.size)

        if arguments['--time']:
            group.append(lhs.c.time)

        if arguments['--extension']:
            group.append(lhs.c.extension)

        if arguments['--basename']:
            group.append(lhs.c.basename)

        if arguments['--quick']:
            group.append(lhs.c.hash_quick)

        if arguments['--full']:
            group.append(lhs.c.hash_total)

        if len(group) != 0:
            sel = sel.group_by(group)

        return sel

    # ToDo: Add tests for each combination
    args = set(chain(*(re.findall(r'\{[A-Z]+\}', arg) for arg in arguments['COMMAND'])))
    if args == {'{LHS}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{LHS}', '{RHS}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHS'), rhs.c.path.label('RHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(lhs.c.path).order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{LHS}', '{RHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHS'), func.group_concat(rhs.c.path).label('RHSGROUP')])
            sel = match(sel, lhs, rhs)
            sel = sel.group_by(lhs.c.path)
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{LHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('LHSGROUP')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(lhs.c.path)
            return sel
    elif args == {'{LHSGROUP}', '{RHS}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('LHSGROUP'), rhs.c.path.label('RHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.group_by(rhs.c.path)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{LHSGROUP}', '{RHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('LHSGROUP'), func.group_concat(rhs.c.path).label('RHSGROUP')])
            sel = match(sel, lhs, rhs)
            sel = match_group(sel, lhs, rhs)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{LHSONLY}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHS')])
            sel = sel.where(not exists(
                match(select([rhs.c.path]), lhs, rhs)
            ))
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{LHSONLYGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('LHSGROUP')])
            sel = sel.where(not exists(
                match(select([rhs.c.path]), lhs, rhs)
            ))
            sel = sel.order_by(lhs.c.path)
            return sel
    elif args == {'{RHS}'}:
        def get_sel(lhs, rhs):
            sel = select([rhs.c.path.label('RHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{RHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(rhs.c.path).label('RHSGROUP')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(rhs.c.path)
            return sel
    elif args == {'{RHSONLY}'}:
        def get_sel(lhs, rhs):
            sel = select([rhs.c.path.label('RHS')])
            sel = sel.where(not exists(
                match(select([lhs.c.path]), lhs, rhs)
            ))
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif args == {'{RHSONLYGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(rhs.c.path).label('LHSGROUP')])
            sel = sel.where(not exists(
                match(select([lhs.c.path]), lhs, rhs)
            ))
            sel = sel.order_by(rhs.c.path)
            return sel
    elif args == {'{DUPE}'}:
        # ToDo: Work out how to handle dupe/unique
        raise DocoptExit('DUPE not implemented yet')
    elif args == {'{DUPEGROUP}'}:
        raise DocoptExit('DUPEGROUP not implemented yet')
    elif args == {'{UNIQUE}'}:
        raise DocoptExit('UNIQUE not implemented yet')
    elif args == {'{UNIQUEGROUP}'}:
        raise DocoptExit('UNIQUEGROUP not implemented yet')
    else:
        raise DocoptExit('COMMAND does not contain a valid combination of special arguments')

    engine = create(None)
    with engine_dispose(engine):


        lhsrwFiles, lhsroFiles = attach_side(engine, 'lhs', arguments['--lhs-db'], arguments['--lhs-update'], arguments['--lhs-path'])
        rhsrwFiles, rhsroFiles = attach_side(engine, 'rhs', arguments['--rhs-db'], arguments['--rhs-update'], arguments['--rhs-path'])

        if not arguments['--none'] and (lhsrwFiles != None or rhsrwFiles != None):
            # Do a preliminary comparison
            lhssel = match(select([lhsroFiles.c.path]), lhsroFiles, rhsroFiles)
            rhssel = match(select([rhsroFiles.c.path]), lhsroFiles, rhsroFiles)

            # Update rw table
            conn = engine.connect()

            def updaterw(ro,rw,sel):
                for result in conn.execute(sel):
                    file = conn.execute(rw.select().where(rw.c.path == result.path)).fetchone()
                    try:
                        stat = os.stat(result.path, follow_symlinks=False)
                    except Exception:
                        hash_quick, hash_total = None, None
                    else:
                        hash_quick, hash_total = hashfile(result.path, stat, arguments['--quick'])

                    if hash_quick != None or hash_total != None:
                        conn.execute(rw.update().where(rw.c.path == result.path).values(
                            size = stat.st_size,
                            time = stat.st_mtime_ns,
                            hash_quick = hash_quick,
                            hash_total = hash_total
                        ))
                    else:
                        conn.execute(rw.delete().where(rw.c.path == result.path))
            try:
                updaterw(lhsroFiles, lhsrwFiles, lhssel)
                updaterw(rhsroFiles, rhsrwFiles, rhssel)
            finally:
                conn.close()

        # Do the full comparison

        sel = get_sel(
            lhsroFiles if lhsrwFiles is None else lhsrwFiles,
            rhsroFiles if rhsrwFiles is None else rhsrwFiles
        )

        conn = engine.connect()
        try:
            for result in conn.execute(sel):
                cmd = [re.sub(r'\{([A-Z]+)\}', (lambda match: result[match.group(1)]), arg) for arg in arguments['COMMAND']]
                print(cmd)
                #ToDo: Execute command
        finally:
            conn.close()
