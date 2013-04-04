#!/usr/bin/env python

import sys

sys.path.append('../../')

from fabricate import *

def build():
    # Make lots of directories to check ordered delete
    run('mkdir', 'testdir')
    run('mkdir', 'testdir/a')
    run('mkdir', 'testdir/b')
    run('mkdir', 'testdir/c')
    run('mkdir', 'testdir/c/f')
    run('mkdir', 'testdir/c/e')
    run('mkdir', 'testdir/c/d')
    
    # put some files in them to ensure content deleted before dir
    run('touch', 'testdir/f1')
    run('touch', 'testdir/f2')
    run('touch', 'testdir/b/f1')
    run('touch', 'testdir/b/f2')
    run('touch', 'testdir/c/d/f1')
    run('touch', 'testdir/c/d/f2')

    # make a dir that alreay exists
    run('mkdir', '-p', 'testdir/c/d')
    
    # make a dir that already partialy exists
    run('mkdir', '-p', 'testdir/c/g')
    
    # make a dir that already partialy exists but should not be deleted
    run('mkdir', '-p', 'existingdir/a')
    
  
def clean():
	autoclean()

main()
