#!/usr/bin/env python

import sys

sys.path.append('../../')

from fabricate import *

def build():
    run('tar', 'czvf', 'foo.tar.gz', 'a.c', 'b.c')
	 
def clean():
	autoclean()

main()
