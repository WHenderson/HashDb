import hashlib as HASHLIB
from collections import namedtuple

HASHBLOCK_QUICK = 64*1024

FileHash = namedtuple('FileHash', 'hash_quick hash_total')
def hash(path, size, quick=False):
    if size == 0:
        # doesn't just speed up zero byte files. Unending files are reported as 0 bytes long, so this prevents us from getting stuck in an unending read
        return FileHash(
            'd41d8cd98f00b204e9800998ecf8427e',
            'd41d8cd98f00b204e9800998ecf8427e'
        )
    
    try:
        hash_quick = None
        hash_total = None
       
        with open(path, 'rb') as f:
            
            if size <= HASHBLOCK_QUICK*2:
                # can do all hashes in one
                hasher = HASHLIB.md5()
                hasher.update(f.read(size))
                hash_quick = hash_total = hasher.hexdigest()
            else:
                hasher = HASHLIB.md5()
                hasher.update(f.read(HASHBLOCK_QUICK))
                f.seek(size - HASHBLOCK_QUICK)
                hasher.update(f.read(HASHBLOCK_QUICK))
                hash_quick = hasher.hexdigest()
                
                if not quick:
                    f.seek(0)
                    while True:
                        data = f.read(HASHBLOCK_QUICK)
                        if not data:
                            break
                        hasher.update(data)
                    hash_total = hasher.hexdigest()
        return FileHash(
            hash_quick = hash_quick,
            hash_total = hash_total
        )
    except OSError, ex:
        pass
    except IOError, ex:
        pass

    return None