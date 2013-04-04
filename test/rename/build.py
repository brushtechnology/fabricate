#!/usr/bin/env python

import sys

sys.path.append('../../')

from fabricate import *

def build():
    run('mv', 'originalfile', 'testfile')
	 
def clean():
	autoclean()
	# remake the original file
	shell('touch', 'originalfile')

main()
