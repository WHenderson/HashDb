import os.path as PATH

def path_2_tuple(path):
    if isinstance(path, basestring):
        path = path.split(PATH.sep)
    path = tuple(path)
    if path[-1] == '':
        path = path[:-1]
    return path

def path_2_string(path):
    if not isinstance(path, basestring):
        if len(path) == 1:
            path = tuple(path) + ('',)
        return PATH.sep.join(path)
    return path

def iterpath(path, reversed=False):
    for part in iterpath_tuple(path, reversed=reversed):
        yield path_2_string(part)

def iterpath_tuple(path, reversed=False):
    path = path_2_tuple(path)
    if not reversed:
        yield path[:1]
        for x in range(1, len(path), 1):
            yield path[:x+1]
    else:
        for x in range(len(path), 1, -1):
            yield path[:x]
        yield path[:1]
