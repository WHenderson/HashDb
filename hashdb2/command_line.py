'''
HashDb2

Usage:
    hashdb2 -h | --help
    hashdb2 --version
    hashdb2 hash [-f|-q|-n] DATABASE -- INPUTS...
    hashdb2 comp [-f|-q|-n] [-steb0cid] [--separator SEP] ((--lhs-db LHSDB [(--lhs-path LHSPATH [--lhs-update])]) | --lhs-path LHSPATH) [(--rhs-db RHSDB ([--rhs-path RHSPATH [--rhs-update]])) | --rhs-path RHSPATH] -- COMMAND...

Options:
    hash                  Create/Update DATABASE with INPUTS
    comp                  Compare inputs, executing COMMAND for each result according to the special arguments provided to COMMAND

    -f, --full            Generate/Compare complete hash
    -q, --quick           Generate/Compare quick hash
    -n, --none            Do not generate/compare hashes [default]

    -s, --size            Compare using size
    -t, --time            Compare using modification time

    -e, --extension       Compare using file extension
    -b, --basename        Compare using basename
    
    -0, --skip-empty      Skip empty files
    
    -c, --echo            Echo command before execution
    -i, --ignore-errors   Ignore errors when executing command
    -d, --dry-run         Echo command but do not run it

    --lhs-db LHSDB        Left database input
    --lhs-update          Update left database as required
    --lhs-path LHSPATH    Left sub-path

    --rhs-db RHSDB        Right database input
    --rhs-update          Update right database as required
    --rhs-path RHSPATH    Right sub-path
    
    --separator SEP       Separator used in GROUP results [default: ,]

    DATABASE              Name of the database to create/update
    INPUTS                List files/folders to add to DATABASE
    COMMAND               Command which is executed according to matched groups
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
                          {UNIQUE}
                          {UNIQUEGROUP}
    
                          LHS and RHS specifies the input
                          The GROUP suffix combines items into a list using the separator specified by --separator.
                          The ONLY suffix finds elements which have no match
    
                          Use DUPE to get inputs which have duplicates (not valid with rhs)
                          Use UNIQUE to get inputs which are unique  (not valid with rhs)
                          
                          In addition, each of the special names above can be suffixed with one of the following:
                          
                          dirpath         full folder path
                          basename        full basename including extension
                          ext             file extension (including the '.')
                          name            basename, excluding the extension
                          drive           drive
                          dirpathnodrive  full folder path, without the drive
                          fullpath        full path
                          
                          eg:
                          
                          {LHS:basename}
                          {RHSGROUP:dirpath}
'''

from docopt import docopt

import pkg_resources  # part of setuptools
version = pkg_resources.require("hashdb2")[0].version

import sys

def main(argv=None, fcapture=None):
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
    elif arguments['comp']:
        from .command_comp import command_comp
        command_comp(arguments, fcapture=fcapture)

if __name__ == '__main__':
    main()
