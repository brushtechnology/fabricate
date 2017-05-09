#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pytest
import plumbum.cmd as sh
from plumbum import local
import os
from copy import copy


from fabricate import *
from fabricate import md5func
from conftest import *

EMPTY_FILE_MD5 = 'd41d8cd98f00b204e9800998ecf8427e'

def test_md5_hasher(builddir):
    with local.cwd(builddir):
        sh.touch('testfile')
        sh.mkdir('testdir')
        sh.touch('testdir/testfile')
        sh.ln('-s', 'testdir', 'testdirlink')
        sh.ln('-s', 'testfile', 'testlink')
        sh.ln('-s', 'nofile', 'testlink_nofile')
        assert md5_hasher('nofile') == None
        assert md5_hasher('testfile') == EMPTY_FILE_MD5
        assert md5_hasher('testdir') == md5func('testdir'.encode('utf-8')).hexdigest()
        assert md5_hasher('testlink') == EMPTY_FILE_MD5
        assert md5_hasher('testdirlink') == md5func('testdir'.encode('utf-8')).hexdigest()
        assert md5_hasher('testlink_nofile') == md5func('nofile'.encode('utf-8')).hexdigest()


