from .orm import create, create_schema
from .walk import walk
from sqlalchemy import MetaData, Table, func, and_
import os.path
from stat import S_ISREG
from .hash import hashfile, HASH_ZERO

def command_hash(arguments, engine=None, schema='main'):
    if engine is None:
        engine = create(arguments['DATABASE'])

    create_schema(engine, schema)

    metadata = MetaData(schema=schema)
    Files = Table('Files', metadata, autoload=True, autoload_with=engine)

    conn = engine.connect()

    try:
        for input in arguments['INPUTS']:
            input = os.path.realpath(input)

            for inputRoot, inputFolders, inputFiles in walk(input, followlinks=False, skiplinks=True):
                badFiles = set()

                for inputFile in inputFiles:
                    print('inputFile:', inputFile)
                    try:
                        print('stat')
                        stat = inputFile.stat(follow_symlinks=False)
                    except Exception as ex:
                        print(ex)
                        badFiles.add(inputFile)
                        continue

                    if not S_ISREG(stat.st_mode):
                        print('!S_ISREG')
                        badFiles.add(inputFile)
                        continue

                    size = stat.st_size
                    time = stat.st_mtime_ns
                    file = conn.execute(Files.select().where(Files.c.path == inputFile.path)).fetchone()

                    if file is None or size != file.size or time != file.time or (arguments['--quick'] and file.hash_quick is None) or (arguments['--full'] and file.hash_total is None):
                        # calculate changes
                        path = inputFile.path
                        name = inputFile.name
                        extension = os.path.splitext(name)[1]
                        hash_quick = None
                        hash_total = None

                        if size == 0:
                            hash_quick = HASH_ZERO
                            hash_total = HASH_ZERO
                        elif arguments['--quick'] or arguments['--full']:
                            hash_quick, hash_total = hashfile(path, stat, not arguments['--full'])
                            if hash_quick is None and hash_total is None:
                                badFiles.add(inputFile)
                                continue

                        if file is None:
                            upsert = Files.insert().values(path=path, name=name, extension=extension)
                        else:
                            upsert = Files.update().where(Files.c.path==path)

                        conn.execute(upsert.values(
                            size=size,
                            time=time,
                            hash_quick=hash_quick,
                            hash_total=hash_total
                        ))

                # Are we only updating multiple files?
                # Note: When a single file update is manually requested, don't do deletes
                if not (len(inputFiles) == 1 and inputFiles[0].path == input):
                    # Delete everything under root which wasn't found by the walk

                    basePath = os.path.join(inputRoot, '')

                    sql = Files.delete()
                    sql = sql.where(func.substr(Files.c.path, 1, len(basePath)) == basePath)

                    # delete any folders not found by the walk
                    if len(inputFolders) != 0:
                        sql = sql.where(and_(*(
                            func.substr(Files.c.path, 1, len(os.path.join(inputFolder.path, ''))) != os.path.join(inputFolder.path, '') for inputFolder in inputFolders
                        )))

                    # delete any files not found by the walk AND delete any files we couldn't hash
                    wantedFiles = [file for file in inputFiles if file not in badFiles]
                    if len(wantedFiles) != 0:
                        sql = sql.where(Files.c.path.notin_([unwantedFile.path for unwantedFile in wantedFiles]))

                    conn.execute(sql)
                elif len(badFiles) != 0:
                    conn.execute(Files.delete().where(Files.c.path == input))
    finally:
        conn.close()
