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

            #engine.execute(CreateView(ro, sel))
            #roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)
            roFiles = sel.cte(ro)

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

            #engine.execute(CreateView(ro, sel))
            #roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)
            roFiles = sel.cte(ro)

            return None, roFiles
    else:
        # rw = fresh memory database
        # ro = view f lhsrw

        attach(engine, rw)
        create_schema(engine, rw)
        rwFiles = Table('Files', MetaData(schema=rw), autoload=True, autoload_with=engine)

        #engine.execute(CreateView(ro, rwFiles.select()))
        #roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)
        roFiles = rwFiles.select().cte(ro)

        if subpath:
            command_hash({'INPUTS': [subpath], '--quick': False, '--full': False, '--none': True}, engine=engine, schema=rw)

        return rwFiles, roFiles

def create_side(dbpath, update, subpath):
    db = rw = 'main'
    ro = 'ro'

    if dbpath:
        exists = os.path.exists(dbpath)

        if update or not exists:

            if not exists:
                touch(dbpath)

            engine = create(dbpath)

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

            #engine.execute(CreateView(ro, sel))
            #roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)
            roFiles = sel.cte(ro)
            rhsroFiles = sel.cte('rhsro')

            return engine, rwFiles, roFiles, rhsroFiles
        else:
            engine = create(dbpath)

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

            #engine.execute(CreateView(ro, sel))
            #roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)
            roFiles = sel.cte(ro)
            rhsroFiles = sel.cte('rhsro')

            return engine, None, roFiles, rhsroFiles
    else:
        # rw = fresh memory database
        # ro = view f lhsrw

        engine = create(None)
        create_schema(engine, rw)
        rwFiles = Table('Files', MetaData(schema=rw), autoload=True, autoload_with=engine)

        #engine.execute(CreateView(ro, rwFiles.select()))
        #roFiles = Table(ro, MetaData(), autoload=True, autoload_with=engine)
        roFiles = rwFiles.select().cte(ro)
        rhsroFiles = rwFiles.select().cte('rhsro')

        if subpath:
            command_hash({'INPUTS': [subpath], '--quick': False, '--full': False, '--none': True}, engine=engine, schema=rw)

        return engine, rwFiles, roFiles, rhsroFiles

def command_comp(arguments, fcapture=None):

    if not any(arguments[name] for name in ('--full', '--quick', '--none', '--size', '--time', '--extension', '--basename')):
        arguments['--full'] = True
        arguments['--extension'] = True

    if not any(arguments[name] for name in ('--full', '--quick', '--none')):
        arguments['--none'] = True

    if not arguments['--none']:
        arguments['--size'] = True

    if arguments['--lhs-update'] and arguments['--lhs-path']:
        arguments['--lhs-path'] = os.path.realpath(arguments['--lhs-path'])

    if arguments['--rhs-update'] and arguments['--rhs-path']:
        arguments['--rhs-path'] = os.path.realpath(arguments['--rhs-path'])

    haslhs = arguments['--lhs-path'] or arguments['--lhs-db']
    hasrhs = arguments['--rhs-path'] or arguments['--rhs-db']

    if (haslhs and hasrhs) or not arguments['--lhs-db']:
        attach = True
    else:
        attach = False

    def match(sel, lhs, rhs, complete=True):
        if arguments['--size']:
            sel = sel.where(lhs.c.size == rhs.c.size)

        if arguments['--time']:
            sel = sel.where(lhs.c.time == rhs.c.time)

        if arguments['--extension']:
            sel = sel.where(lhs.c.extension == rhs.c.extension)

        if arguments['--basename']:
            sel = sel.where(lhs.c.basename == rhs.c.basename)

        if complete:
            if arguments['--quick']:
                sel = sel.where(and_(
                    lhs.c.hash_quick == rhs.c.hash_quick,
                    lhs.c.hash_quick != None
                ))

            if arguments['--full']:
                sel = sel.where(and_(
                    lhs.c.hash_total == rhs.c.hash_total,
                    lhs.c.hash_total != None
                ))

        # Not looking for the actual same file
        sel = sel.where(lhs.c.path != rhs.c.path)

        return sel

    # ToDo: Add tests for each combination
    args = set(chain(*(re.findall(r'\{[A-Z]+\}', arg) for arg in arguments['COMMAND'])))
    if haslhs and hasrhs and args == {'{LHS}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{LHS}', '{RHS}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHS'), rhs.c.path.label('RHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(lhs.c.path).order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{LHS}', '{RHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHS'), func.group_concat(rhs.c.path).label('RHSGROUP')])
            sel = match(sel, lhs, rhs)
            sel = sel.group_by(lhs.c.path)
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{LHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('LHSGROUP')])
            sel = match(sel, lhs, rhs)
            sel = sel.group_by(rhs.c.path)
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{LHSGROUP}', '{RHS}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('LHSGROUP'), rhs.c.path.label('RHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.group_by(rhs.c.path)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{LHSGROUP}', '{RHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path.distinct()).label('LHSGROUP'), func.group_concat(rhs.c.path.distinct()).label('RHSGROUP')])
            #ToDo: fix the ordering of the group items and the overall result set
            #sel = select([lhs.c.path.label('LHSGROUP'), rhs.c.path.label('RHSGROUP')])

            sel = match(sel, lhs, rhs)

            if arguments['--size']:
                sel = sel.group_by(lhs.c.size).order_by(lhs.c.size)

            if arguments['--time']:
                sel = sel.group_by(lhs.c.time).order_by(lhs.c.time)

            if arguments['--extension']:
                sel = sel.group_by(lhs.c.extension).order_by(lhs.c.extension)

            if arguments['--basename']:
                sel = sel.group_by(lhs.c.basename).order_by(lhs.c.basename)

            if arguments['--quick']:
                sel = sel.group_by(lhs.c.hash_quick).order_by(lhs.c.hash_quick)

            if arguments['--full']:
                sel = sel.group_by(lhs.c.hash_total).order_by(lhs.c.hash_total)

            sel = sel.order_by(lhs.c.path)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{LHSONLY}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('LHSONLY')])
            sel = sel.where(~exists(
                match(select(['*']), lhs, rhs)
            ))
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{LHSONLYGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('LHSONLYGROUP')])
            sel = sel.where(~exists(
                match(select(['*']), lhs, rhs)
            ))
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{RHS}'}:
        def get_sel(lhs, rhs):
            sel = select([rhs.c.path.label('RHS')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{RHSGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(rhs.c.path).label('RHSGROUP')])
            sel = match(sel, lhs, rhs)
            sel = sel.group_by(lhs.c.path)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{RHSONLY}'}:
        def get_sel(lhs, rhs):
            sel = select([rhs.c.path.label('RHSONLY')])
            sel = sel.where(~exists(
                match(select(['*']), lhs, rhs)
            ))
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and hasrhs and args == {'{RHSONLYGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(rhs.c.path).label('RHSONLYGROUP')])
            sel = sel.where(~exists(
                match(select(['*']), lhs, rhs)
            ))
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and not hasrhs and args == {'{DUPE}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('DUPE')])
            sel = match(sel, lhs, rhs)
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and not hasrhs and args == {'{DUPEGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path.distinct()).label('DUPEGROUP')])
            sel = match(sel, lhs, rhs)

            if arguments['--size']:
                sel = sel.group_by(lhs.c.size).order_by(lhs.c.size)

            if arguments['--time']:
                sel = sel.group_by(lhs.c.time).order_by(lhs.c.time)

            if arguments['--extension']:
                sel = sel.group_by(lhs.c.extension).order_by(lhs.c.extension)

            if arguments['--basename']:
                sel = sel.group_by(lhs.c.basename).order_by(lhs.c.basename)

            if arguments['--quick']:
                sel = sel.group_by(lhs.c.hash_quick).order_by(lhs.c.hash_quick)

            if arguments['--full']:
                sel = sel.group_by(lhs.c.hash_total).order_by(lhs.c.hash_total)

            sel = sel.order_by(lhs.c.path)
            sel = sel.order_by(rhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and not hasrhs and args == {'{UNIQUE}'}:
        def get_sel(lhs, rhs):
            sel = select([lhs.c.path.label('UNIQUE')])
            sel = sel.where(~exists(
                match(select(['*']), lhs, rhs)
            ))
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    elif haslhs and not hasrhs and args == {'{UNIQUEGROUP}'}:
        def get_sel(lhs, rhs):
            sel = select([func.group_concat(lhs.c.path).label('UNIQUEGROUP')])
            sel = sel.where(~exists(
                match(select(['*']), lhs, rhs)
            ))
            sel = sel.order_by(lhs.c.path)
            sel = sel.distinct()
            return sel
    else:
        raise DocoptExit('COMMAND does not contain a valid combination of special arguments')

    lhsrwFiles, lhsroFiles = None, None
    rhsrwFiles, rhsroFiles = None, None

    print('create')
    if attach:
        engine = create(None)
    else:
        engine, lhsrwFiles, lhsroFiles, rhsroFiles = create_side(arguments['--lhs-db'], arguments['--lhs-update'], arguments['--lhs-path'])

    print('with')
    with engine_dispose(engine):
        if attach:
            print('attach')
            if haslhs:
                lhsrwFiles, lhsroFiles = attach_side(engine, 'lhs', arguments['--lhs-db'], arguments['--lhs-update'], arguments['--lhs-path'])
            if hasrhs:
                rhsrwFiles, rhsroFiles = attach_side(engine, 'rhs', arguments['--rhs-db'], arguments['--rhs-update'], arguments['--rhs-path'])

        if not arguments['--none'] and (lhsrwFiles != None or rhsrwFiles != None):
            # Do a preliminary comparison
            lhssel = match(select([lhsroFiles.c.path]), lhsroFiles, rhsroFiles, False)
            rhssel = match(select([rhsroFiles.c.path]), lhsroFiles, rhsroFiles, False)

            if arguments['--quick']:
                lhssel = lhssel.where(lhsroFiles.c.hash_quick == None)
                rhssel = rhssel.where(rhsroFiles.c.hash_quick == None)

            if arguments['--full']:
                lhssel = lhssel.where(lhsroFiles.c.hash_total == None)
                rhssel = rhssel.where(rhsroFiles.c.hash_total == None)

            # Update rw table
            conn = engine.connect()

            def updaterw(ro,rw,sel):
                if rw is None:
                    return

                for result in conn.execute(sel):
                    print('update result:', result)
                    file = conn.execute(rw.select().where(rw.c.path == result.path)).fetchone()
                    try:
                        print('stat')
                        stat = os.stat(result.path, follow_symlinks=False)
                    except Exception as ex:
                        print('ex:', ex)
                        hash_quick, hash_total = None, None
                    else:
                        print('hash')
                        hash_quick, hash_total = hashfile(result.path, stat, arguments['--quick'])

                    if hash_quick != None or hash_total != None:
                        print('update meta data')
                        conn.execute(rw.update().where(rw.c.path == result.path).values(
                            size = stat.st_size,
                            time = stat.st_mtime_ns,
                            hash_quick = hash_quick,
                            hash_total = hash_total
                        ))
                    else:
                        print('delete')
                        conn.execute(rw.delete().where(rw.c.path == result.path))
            try:
                print('update')
                updaterw(lhsroFiles, lhsrwFiles, lhssel)
                updaterw(rhsroFiles, rhsrwFiles, rhssel)
            except Exception as ex:
                print('ex:', ex)
                raise ex
            finally:
                conn.close()

        # Do the full comparison

        print('gen sel')
        sel = get_sel(
            lhsroFiles if lhsrwFiles is None else lhsrwFiles,
            rhsroFiles if rhsrwFiles is None else rhsrwFiles
        )

        conn = engine.connect()
        try:
            print('sel all')
            for result in conn.execute('select * from Files order by path'):
                print(result)
            print('match')
            for result in conn.execute(sel):
                cmd = [re.sub(r'\{([A-Z]+)\}', (lambda match: result[match.group(1)]), arg) for arg in arguments['COMMAND']]

                if fcapture != None:
                    fcapture(cmd)
                else:
                    print(cmd)
                    #ToDo: Execute command
        except Exception as ex:
            print('ex:', ex)
            raise ex
        finally:
            conn.close()
