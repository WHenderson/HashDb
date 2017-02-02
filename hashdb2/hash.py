import hashlib as HASHLIB
import os as OS
from stat import S_ISREG
from collections import namedtuple

HASHBLOCK_QUICK = 64*1024
HASH_ZERO = 'd41d8cd98f00b204e9800998ecf8427e'

PROGRESS_START   = 0
PROGRESS_HASHING = 1
PROGRESS_DONE    = 2

HashDigest = namedtuple('HashDigest', 'hash_quick hash_total')

def hashfile(path, entryStat, quick, progress=None):
    hasher = HASHLIB.md5()

    try:
        if entryStat is None:
            entryStat = OS.stat(path)
        if not S_ISREG(entryStat.st_mode):
            return HashDigest(None, None)
        if entryStat.st_size == 0:
            return HashDigest(HASH_ZERO, HASH_ZERO)

        with open(path, 'rb') as fin:
            if entryStat.st_size <= HASHBLOCK_QUICK*3:
                # Quick and Total are the same hash
                hasher.update(fin.read(entryStat.st_size))
                hexdigest = hasher.hexdigest()
                return HashDigest(hexdigest, hexdigest)
            else:
                # Do the 'quick' part of the hash

                # start
                hasher.update(fin.read(HASHBLOCK_QUICK))
                if not quick:
                    total_start  = fin.tell()
                    total_hasher = hasher.copy()

                # middle
                fin.seek(HASHBLOCK_QUICK + (entryStat.st_size - HASHBLOCK_QUICK*3)//2)
                hasher.update(fin.read(HASHBLOCK_QUICK))

                # end
                fin.seek(entryStat.st_size - HASHBLOCK_QUICK)
                hasher.update(fin.read(HASHBLOCK_QUICK))

                hexdigest_quick = hasher.hexdigest()
                hexdigest_total = None

                if not quick:
                    if progress:
                        progress(path, 0, PROGRESS_START)

                    fin.seek(total_start)
                    while True:
                        data = fin.read(HASHBLOCK_QUICK)
                        if not data:
                            break

                        if progress:
                            progress(path, fin.tell(), PROGRESS_HASHING)

                        total_hasher.update(data)

                    if progress:
                        progress(path, fin.tell(), PROGRESS_DONE)
                    hexdigest_total = total_hasher.hexdigest()

                return HashDigest(hexdigest_quick, hexdigest_total)
    except Exception as ex:
        return HashDigest(None, None)
