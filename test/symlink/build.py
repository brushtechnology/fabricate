#!/usr/bin/env python

import sys

sys.path.append('../../')

from fabricate import *

def build():
    run('ln', '-s', 'testfile', 'testlink')
    run('ln', '-s', 'testdir', 'testlink_dir')
    run('ln', '-s', 'nofile', 'testlink_nofile')
	 
def clean():
    autoclean()

main()
