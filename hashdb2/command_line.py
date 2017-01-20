'''
HashDb2

Usage:
    hashdb2 -h | --help
    hashdb2 --version
'''


from docopt import docopt

import pkg_resources  # part of setuptools
version = pkg_resources.require("MyProject")[0].version

def main():
    global __doc__
    arguments = docopt(__doc__, version='HashDb2 ' + version)
