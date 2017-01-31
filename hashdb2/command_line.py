'''
HashDb2

Usage:
    hashdb2 -h | --help
    hashdb2 --version
    hashdb2 hash [-f|-q|-n] DATABASE -- INPUTS...
    hashdb2 comp [-stfqneb] LHS [RHS] -- COMMAND...

Options:
    hash             Create/Update DATABASE with INPUTS
    comp             Compare inputs, executing COMMAND for each result according to the special arguments provided to COMMAND

    -f, --full       Generate/Compare complete hash
    -q, --quick      Generate/Compare quick hash
    -n, --none       Do not generate/compare hashes [default]

    -s, --size       Compare using size [default]
    -t, --time       Compare using modification time

    -e, --extension  Compare using file extension [default]
    -b, --basename   Compare using basename

    DATABASE         Name of the database to create/update
    INPUTS           List files/folders to add to DATABASE
    LHS              Left input
    RHS              Right input
    COMMAND          Command which is executed according to matched groups
                     The following values within command have special meaning:

                     {LHS}
                     {LHS} {RHS}
                     {LHS} {RHSGROUP}
                     {LHSGROUP}
                     {LHSGROUP} {RHS}
                     {LHSGROUP} {RHSGROUP}
                     {LHSONLY}
                     {LHSONLYGROUP}
                     {RHS}
                     {RHSGROUP}
                     {RHSONLY}
                     {RHSONLYGROUP}
                     {DUPE}
                     {DUPEGROUP}

                     LHS and RHS specifies the input
                     GROUP provides a list inputs, no GROUP provides them one at a team
                     Use ONLY to get inputs which have no match
                     Use DUPE to get inputs which have duplicates in any database
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
