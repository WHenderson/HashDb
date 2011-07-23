#!/usr/bin/python

if __name__ == '__main__':
    from hashdb_cmdline import parser_build
    
    # build parser
    parser = parser_build()
    # parse args
    cmdline = parser.parse_args()
    # execute command
    cmdline.command(**vars(cmdline))