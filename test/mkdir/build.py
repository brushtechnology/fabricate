#!/usr/bin/env python

import sys

sys.path.append('../../')

from multiprocessing import freeze_support
from fabricate import *

def build():
    # Make lots of directories to check ordered delete
    run('mkdir', 'testdir', group='testdir')
    run('mkdir', 'testdir/a', group='a', after='testdir')
    run('mkdir', 'testdir/b', group='b', after='testdir')
    run('mkdir', 'testdir/c', group='c', after='testdir')
    run('mkdir', 'testdir/c/f', group='f', after='c')
    run('mkdir', 'testdir/c/e', group='e', after='c')
    run('mkdir', 'testdir/c/d', group='d', after='c')
    
    # put some files in them to ensure content deleted before dir
    run('touch', 'testdir/f1', after='testdir')
    run('touch', 'testdir/f2', after='testdir')
    run('touch', 'testdir/b/f1', after='b')
    run('touch', 'testdir/b/f2', after='b')
    run('touch', 'testdir/c/d/f1', after='d')
    run('touch', 'testdir/c/d/f2', after='d')

    # make a dir that alreay exists
    run('mkdir', '-p', 'testdir/c/d', after='d')
    
    # make a dir that already partialy exists
    run('mkdir', '-p', 'testdir/c/g', after='c')
    
    # make a dir that already partialy exists but should not be deleted
    run('mkdir', '-p', 'existingdir/a')
    
  
def clean():
	autoclean()

if __name__ == "__main__":
    freeze_support()
    main(parallel_ok=True)
