'''
HashDb2

Usage:
    hashdb2 -h | --help
    hashdb2 --version
    hashdb2 hash [-f|-q|-n] DATABASE -- INPUTS...

Options:
    -f|--full   Generate complete hash for each file
    -q|--quick  Generate quick hash for each file
    -n|--none   Do not generate hashes [default]

    DATABASE    Name of the database to create/update
    INPUTS      List files/folders to add to DATABASE
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
    arguments = docopt(__doc__, argv[1:], version='HashDb2 ' + version)
    print(arguments)

    if arguments['hash']:
        from .command_hash import command_hash
        command_hash(arguments)

if __name__ == '__main__':
    main()
