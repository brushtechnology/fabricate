#!/usr/bin/env python

import sys
import os

sys.path.append('../../')

from fabricate import *

# Run the md5hasher tests
if __name__ == '__main__':

    print md5_hasher('nofile')
    print md5_hasher('testfile')
    print md5_hasher('testdir')
    print md5_hasher('testlink')
    print md5_hasher('testdirlink')
    print md5_hasher('testlink_nofile')
    
    sys.exit(0)
