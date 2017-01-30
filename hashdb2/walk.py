from os import scandir, strerror
from os.path import join, islink, isdir, dirname, basename
from errno import ENOENT

def walk(top, topdown=True, onerror=None, followlinks=False, skiplinks=False):
    onerror = onerror or (lambda err : None)

    if isdir(top):
        yield from _walk(top, topdown, onerror, followlinks, skiplinks)
    else:
        dirpath = dirname(top)
        filename = basename(top)

        try:
            scandir_it = scandir(dirpath)
        except OSError as error:
            onerror(error)
            return

        while True:
            try:
                try:
                    entry = next(scandir_it)
                except StopIteration:
                    raise FileNotFoundError(ENOENT, strerror(ENOENT), filename)
            except OSError as error:
                onerror(error)
                return

            if entry.name == filename:
                if skiplinks:
                    try:
                        is_symlink = entry.is_symlink()
                    except OSError:
                        is_symlink = False

                    if is_symlink:
                        yield dirpath, [], []
                    else:
                        yield dirpath, [], [entry]
                else:
                    yield dirpath, [], [entry]
                return

def _walk(top, topdown=True, onerror=None, followlinks=False, skiplinks=False):
    """Like Python 3.5's implementation of os.walk() -- faster than
    the pre-Python 3.5 version as it uses scandir() internally.
    """
    dirs = []
    nondirs = []

    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        scandir_it = scandir(top)
    except OSError as error:
        onerror(error)
        return

    while True:
        try:
            try:
                entry = next(scandir_it)
            except StopIteration:
                break
        except OSError as error:
            onerror(error)
            return

        try:
            is_dir = entry.is_dir()
        except OSError:
            # If is_dir() raises an OSError, consider that the entry is not
            # a directory, same behaviour than os.path.isdir().
            is_dir = False

        if is_dir:
            dirs.append(entry)
        else:
            if skiplinks:
                try:
                    is_symlink = entry.is_symlink()
                except OSError:
                    is_symlink = False

                if not is_symlink:
                    nondirs.append(entry)
            else:
                nondirs.append(entry)

        if not topdown and is_dir:
            # Bottom-up: recurse into sub-directory, but exclude symlinks to
            # directories if followlinks is False
            if followlinks:
                walk_into = True
            else:
                try:
                    is_symlink = entry.is_symlink()
                except OSError:
                    # If is_symlink() raises an OSError, consider that the
                    # entry is not a symbolic link, same behaviour than
                    # os.path.islink().
                    is_symlink = False
                walk_into = not is_symlink

            if walk_into:
                yield from _walk(entry.path, topdown, onerror, followlinks, skiplinks)

    # Yield before recursion if going top down
    if topdown:
        yield top, dirs, nondirs

        # Recurse into sub-directories
        for entry in dirs:
            new_path = join(top, entry.name)
            # Issue #23605: os.path.islink() is used instead of caching
            # entry.is_symlink() result during the loop on os.scandir() because
            # the caller can replace the directory entry during the "yield"
            # above.
            if followlinks or not islink(new_path):
                yield from _walk(new_path, topdown, onerror, followlinks, skiplinks)
    else:
        # Yield after recursion if going bottom up
        yield top, dirs, nondirs
