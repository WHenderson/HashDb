import os.path
import re

class FilePath:
    def __init__(self, fullpath):
        self.fullpath = fullpath

    @property
    def dirpath(self):
        return os.path.dirname(self.fullpath)

    @property
    def basename(self):
        return os.path.basename(self.fullpath)

    @property
    def ext(self):
        return os.path.splitext(self.fullpath)[1]

    @property
    def name(self):
        return os.path.splitext(self.basename)[0]

    @property
    def drive(self):
        return os.path.splitdrive(self.fullpath)[0]

    @property
    def dirpathnodrive(self):
        return os.path.splitdrive(self.dirpath)[1]

    def __str__(self):
        return self.fullpath

    def __repr__(self):
        return self.fullpath

    @staticmethod
    def splitpaths(filepaths, separator):
        return [
            FilePath(p.replace(separator + separator, separator))
            for p in re.findall('(?:(?!%(sep)s).|(?:%(sep)s%(sep)s))+' % {'sep': separator}, filepaths)
        ]

    @staticmethod
    def joinpaths(filepaths, separator):
        result = [p.replace(separator, separator + separator) for p in filepaths]
        result.sort()
        return separator.join(result)

def gen_group_filepath(separator):
    class GroupFilePath:
        def __init__(self):
            self._paths = set()
            self._separator = separator

        def step(self, value):
            self._paths.add(value)

        def finalize(self):
            return FilePath.joinpaths(sorted(self._paths), self._separator)

    return GroupFilePath
