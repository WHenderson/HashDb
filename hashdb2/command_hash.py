from .orm import create, create_schema
from .walk import walk
from sqlalchemy import MetaData, Table, func, and_
import os.path
from stat import S_ISREG
from .hash import hashfile

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
                    try:
                        stat = inputFile.stat(follow_symlinks=False)
                    except Exception:
                        badFiles.add(inputFile)
                        continue

                    if not S_ISREG(stat.st_mode):
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

                        if arguments['--quick'] or arguments['--full']:
                            hash_quick, hash_total = hashfile(path, inputFile.stat(follow_symlinks=False), not arguments['--full'])
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

                # Are we only updating one file?
                if not (len(inputFiles) == 1 and inputFiles[0].path == input):
                    # Delete unwanted files/folders
                    basePath = os.path.join(inputRoot, '')

                    sql = Files.delete()
                    sql = sql.where(func.substr(Files.c.path, 1, len(basePath)) == basePath)

                    if len(inputFolders) != 0:
                        sql = sql.where(and_(*(
                            func.substr(Files.c.path, 1, len(os.path.join(inputFolder.path, ''))) != os.path.join(inputFolder.path, '') for inputFolder in inputFolders
                        )))

                    unwantedFiles = [file for file in inputFiles if file not in badFiles]
                    if len(unwantedFiles) != 0:
                        sql = sql.where(Files.c.path.notin_([unwantedFile.path for unwantedFile in unwantedFiles]))

                    conn.execute(sql)
                elif len(badFiles) != 0:
                    conn.execute(Files.delete().where(Files.c.path == input))
    finally:
        conn.close()
