from .orm import create, create_schema
from .walk import walk
from sqlalchemy import MetaData, Table, func, and_
import os.path

def command_hash(arguments):
    engine = create(arguments['DATABASE'])
    engine = create_schema(engine)

    metadata = MetaData()
    Files = Table('Files', metadata, autoload=True, autoload_with=engine)

    conn = engine.connect()

    try:
        for input in arguments['INPUTS']:
            input = os.path.realpath(input)

            for inputRoot, inputFolders, inputFiles in walk(input, followlinks=False, skiplinks=True):
                for inputFile in inputFiles:
                    stat = inputFile.stat(follow_symlinks=False)
                    size = stat.st_size
                    time = stat.st_mtime_ns
                    file = conn.execute(Files.select().where(Files.c.path == inputFile.path)).fetchone()

                    if file is None or size != file.size or time != file.time:
                        # calculate changes
                        path = inputFile.path
                        name = inputFile.name
                        extension = os.path.splitext(name)[1]
                        hash_quick = None
                        hash_total = None

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
                if len(inputFiles) != 1 or inputFiles[0].path != input:
                    # Delete unwanted files/folders
                    basePath = os.path.join(inputRoot, '')

                    sql = Files.delete()
                    sql = sql.where(func.substr(Files.c.path, 1, len(basePath)) == basePath)

                    if len(inputFolders) != 0:
                        sql = sql.where(and_(*(
                            func.substr(Files.c.path, 1, len(os.path.join(inputFolder.path, ''))) != os.path.join(inputFolder.path, '') for inputFolder in inputFolders
                        )))
                    if len(inputFiles) != 0:
                        sql = sql.where(Files.c.path.notin_([inputFile.path for inputFile in inputFiles]))

                    conn.execute(sql)
    finally:
        conn.close()
