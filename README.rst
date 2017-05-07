======
HashDb
======
Command-line utility to quickly scan and compare files/folders, primarily based off of contents.
Comparison results can be fed to a commandline using parameter substitution.

This utility provides a convenient way to find/remove/move duplicate files in a fast and efficient manner.
File meta data, including hash, can be cached on disk, allowing for quick repeated comparisons.

.. image:: https://travis-ci.org/WHenderson/HashDb.svg?branch=master
    :target: https://travis-ci.org/WHenderson/HashDb

Installation
============
::

    pip install hashdb2

Command Line
============
::

  HashDb2

  Usage:
      hashdb2 -h | --help
      hashdb2 --version
      hashdb2 hash [-f|-q|-n] DATABASE -- INPUTS...
      hashdb2 comp [-f|-q|-n] [-steb0cid] ((--lhs-db LHSDB [(--lhs-path LHSPATH [--lhs-update])]) | --lhs-path LHSPATH) [(--rhs-db RHSDB ([--rhs-path RHSPATH [--rhs-update]])) | --rhs-path RHSPATH] -- COMMAND...

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
                            The GROUP suffix combines items into a list
                            The ONLY suffix finds elements which have no match

                            Use DUPE to get inputs which have duplicates (not valid with rhs)
                            Use UNIQUE to get inputs which are unique  (not valid with rhs)

Examples
========

Find and remove duplicates
--------------------------
::

    hashdb2 comp --lhs-path /my-files -- rm {DUPE}

Compare two folders and remove duplicates from one of them
----------------------------------------------------------
::

    hashdb2 comp --lhs-path /keep-these-files --rhs-path /remove-duplicates -- rm {RHS}

Copy missing files
------------------
::

    hashdb2 comp --lhs-path /backup --rhs-path /sdcard -- cp {RHSONLY} /backup/

