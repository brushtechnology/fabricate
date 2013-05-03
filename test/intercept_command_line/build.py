#!/usr/bin/env python

# Test building using when intercepting the command line
# Created for issue 33 testing

if __name__ == '__main__':
    import sys
    sys.path.append('../../')
    import fabricate

    default='myfab'
    
    def myfab():
        fabricate.run('touch', 'testfile')
    
    def clean():
        fabricate.autoclean()
    
    if len(sys.argv) > 1:
        default=sys.argv[1]
    
    fabricate.main(command_line=[default])
