import argparse as ARGPARSE
import hashdb_cmd as CMD

def type_directory(input):
    import os as OS
    import stat as STAT
    
    try:
        stat = OS.stat(input)
        if not STAT.S_ISDIR(stat.st_mode):
            raise ARGPARSE.ArgumentTypeError('target is not a directory')
        return input
    except OSError:
        raise ARGPARSE.ArgumentTypeError('Unable to read target')

def parser_build():
    p_root = ARGPARSE.ArgumentParser(
        prog='hashdb',
        description='Maintains hash values for files within a directory tree. Primarily used for finding duplicates/unique files',
    )

    subparsers = p_root.add_subparsers(
        help='use "<command> -h" to get detailed information on each command'
    )
    
    def add_update_options(subparser):
        group = subparser.add_argument_group(
            title='hash options',
            description='''The following options control how files are hashed once they are located'''
        )
        group.add_argument('-c', '--hash-complete', dest='quick', action='store_false', help='perform complete hash on all files')
        group.add_argument('-q', '--hash-quick', dest='quick', action='store_true', help='perform quick hash on files (hash the begining and the ending of the file)')
        
        group = subparser.add_argument_group(
            title='traversal options',
            description='''The following options control aspects of how the directory tree is traversed'''
        )
        group.add_argument('--symlinks-skip', dest='skip_symlinks', action='store_true', help='do not hash or resolve symlinks')
        group.add_argument('--symlinks-keep', dest='skip_symlinks', action='store_false', help='resolve symlinks')
        group.add_argument('--mounts-skip', dest='skip_mounts', action='store_true', help='do not traverse mount points')
        group.add_argument('--mounts-keep', dest='skip_mounts', action='store_false', help='traverse mount points')
        group.add_argument('--devices-same', dest='skip_devices', action='store_true', help='do not traverse into different devices')
        group.add_argument('--devices-any', dest='skip_devices', action='store_false', help='traverse regardless of devices')

    
    p_anchor = subparsers.add_parser(
        'anchor',
        help='Creates an anchor point in the target directory',
        description='Creates an anchor point in the target directory',
    )
    p_anchor.set_defaults(command=CMD.cmd_anchor)
    p_anchor.add_argument('-U', '--no-update', dest='update', action='store_false', default=True, help='do not update the anchor, just leave it empty')
    add_update_options(p_anchor)
    p_anchor.add_argument('target', metavar='PATH', nargs='?', default='./', action='store', type=type_directory, help='place new anchor point in the specified directory. defaults to the current directory')

    
    p_update = subparsers.add_parser(
        'update',
        help='Updates the hash for all files in the target directories',
        description='Updates the hash for all files in the target directories'
    )
    p_update.set_defaults(command=CMD.cmd_update)
    add_update_options(p_update)
    p_update.add_argument('targets', metavar='PATH', nargs='*', default=['./'], type=type_directory, help='scan for changes within these directories. default is to scan the current directory')
    
    
    p_export = subparsers.add_parser(
        'export',
        help='Exports a database for use on a remote host',
        description='Exports a database for use on a remote host'
    )
    p_export.set_defaults(command=CMD.cmd_export)
    add_update_options(p_export)
    p_export.add_argument('database', metavar='FILENAME', nargs=1, help='store exported hash values into this database. recommended extension is ".hashdb"')
    p_export.add_argument('targets', metavar='PATH', nargs='*', default=['/'], type=type_directory, help='export these directories. default is to export everything.')
    

    p_compare = subparsers.add_parser(
        'compare',
        help='Compares an exported hash database with local directories',
        description='Compares an exported hash database with local directories'
    )
    p_compare.set_defaults(command=CMD.cmd_compare)
    add_update_options(p_compare)
    p_compare.add_argument('database', metavar='FILENAME', nargs=1, help='external hash database to compare against')
    p_compare.add_argument('targets', metavar='PATH', nargs='+', type=type_directory, help='compare with these directories')
    
    
    # this one needs to be defined better, at the moment its too vauge to be of use
    valid_operations = {
        'delete'  : (None, 'deletes secondary'),
        'symlink' : (None, 'creates a symlink from secondary to primary'),
        'rellink' : (None, 'creates a symlink from secondary to primary using relative paths'),
        'abslink' : (None, 'creates a symlink from secondary to primary using absolute paths'),
        'hardlink': (None, 'creates a hardlink between primary and secondary'),
        'print'   : (None, 'prints the relevent information'),
        'ignore'  : (None, 'does nothing'),
        'delete-xdev'  : (None, 'deletes secondary. primary and secondary must be on the same device'),
        'symlink-xdev' : (None, 'creates a symlink from secondary to primary. primary and secondary must be on the same device'),
        'rellink-xdev' : (None, 'creates a symlink from secondary to primary using relative paths. primary and secondary must be on the same device'),
        'abslink-xdev' : (None, 'creates a symlink from secondary to primary using absolute paths. primary and secondary must be on the same device'),
    }
    ambiguous_operations = {
        'ordered' : (None, 'orders the targets according to the primary and secondary targets, then alphabetically, and makes the first target the primary and the remaining targets secondary. Operations then proceed as specified for non-ambiguous targets'),
        'ignore'  : (None, 'does nothing'),
        'print'   : (None, 'prints the relevent information'),
        'hardlink': (None, 'creates a hardlink between all targets'),
    }
    p_duplicates = subparsers.add_parser(
        'duplicates',
        help='Find duplicates',
        formatter_class=ARGPARSE.RawDescriptionHelpFormatter,
        description='''
Searches all speified targets for duplicates. Once duplicates are found, the specified operations are applied in turn until one is successful or none are left.
When specifying targets:
    'primary' targets are not modified.
    'secondary' targets are considered expendable and will be deleted/replaced with a symlink etc according to the chosen operations.
    'ambiguous' targets specified either directly, or indirectly through overlap of primary and secondary, are treated specially using the operations specified by -a/--ambiguous-operation

Operations:
%s
Operations for ambiguous targets:
%s      ''' % (''.join(('    %-13s: %s\n' % (n,v[1])) for n,v in valid_operations.iteritems()), ''.join(('    %-13s: %s\n' % (n,v[1])) for n,v in ambiguous_operations.iteritems()))
    )
    p_duplicates.set_defaults(command=CMD.cmd_duplicates)
    add_update_options(p_duplicates)
    
    p_duplicates.add_argument('--quick-match', dest='exact_match', default=False, action='store_true', help='Only perform a quick match (hash the start and end of a file)')
    p_duplicates.add_argument('-o', '--operation',  dest='op', action='append', default=[], choices=valid_operations, help='select the operation to perform on duplicate matches')
    p_duplicates.add_argument('-a', '--ambiguous-operation',  dest='opa', action='append', default=[], choices=ambiguous_operations, help='select the operation to perform on ambiguous duplicate matches')
    p_duplicates.add_argument('-1', '--primary', metavar='PATH', nargs='+', dest='targets1', default=[], help='primary targets')
    p_duplicates.add_argument('-2', '--secondary', metavar='PATH', nargs='+', dest='targets2', default=[], help='secondary targets')
    p_duplicates.add_argument('targets', metavar='PATH', nargs='*', default=['./'], type=type_directory, help='ambiguous targets')
    
    return p_root