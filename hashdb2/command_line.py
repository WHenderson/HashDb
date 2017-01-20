'''
HashDb2

Usage:
    hashdb2 -h | --help
    hashdb2 --version
'''


from docopt import docopt

import pkg_resources  # part of setuptools
version = pkg_resources.require("hashdb2")[0].version

import sys

def main(argv=None):
    if argv is None:
        argv = sys.argv
    else:
        argv = [__file__] + argv

    global __doc__
    arguments = docopt(__doc__, argv, version='HashDb2 ' + version)
