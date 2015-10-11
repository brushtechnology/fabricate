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
EMPY_FILE_MD5 = 'd41d8cd98f00b204e9800998ecf8427e'




@pytest.mark.parametrize("runner", runner_list)
def test_create(builddir, runner, end_fabricate):
    # prepare needed files
    with local.cwd(builddir):
        (sh.echo["a.c"] > "a.c")()
        (sh.echo["b.c"] > "b.c")()

    # build.py content >>>>>>>>>>>>>>>>>>>>>
    def fabricate_file():
        def build():
            run('tar', 'czvf', 'foo.tar.gz', 'a.c', 'b.c')

        def clean():
            autoclean()
        return copy(locals())

    main(globals_dict=fabricate_file(),
         build_dir=builddir,
         runner=runner,
         command_line=['-c', '-D', 'build'])
    end_fabricate()

    expected_json = {'tar czvf foo.tar.gz a.c b.c':
        {'b.c': 'input-',
         'foo.tar.gz': 'output-',
         'a.c': 'input-'},
     u'.deps_version': 2}


    # assertions
    with local.cwd(builddir):
        assert_same_json('.deps', expected_json)
        assert os.path.isfile('foo.tar.gz')
        assert sh.tar("tf", 'foo.tar.gz') == "a.c\nb.c\n"
        print(sh.ls("-al"))
        assert '"a.c": "input-' in sh.cat(".deps")
        sys.exit.assert_called_once_with(0)


        # Modify a.c to force rebuilding
        (sh.echo["newline"] > "a.c")()

    main(globals_dict=fabricate_file(),
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'build'])
    end_fabricate()

    with local.cwd(builddir):
        sh.tar("df", "foo.tar.gz") # ensure tar diff return no difference


@pytest.mark.parametrize("runner", runner_list)
def test_mkdir(builddir, runner, end_fabricate):

    # build.py content >>>>>>>>>>>>>>>>>>>>>
    def fabricate_file():
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

        return copy(locals())

    with local.cwd(builddir):
        sh.mkdir('existingdir')
        sh.touch('existingdir/existingfile')

    main(globals_dict=fabricate_file(),
         #parallel_ok=True,
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'build'])
    end_fabricate()

    expected_json = {
        ".deps_version": 2,
        "mkdir -p existingdir/a": {
            "existingdir": "input-ae394c47b4ccf49007dc9ec847f657b9",
            "existingdir/a": "output-16873f5a4ba5199a8b51f812d159e37e"
        },
        "mkdir -p testdir/c/d": {
            "testdir": "input-3ca0a3620b59afb57cf5fd77cee6432c",
            "testdir/c": "input-54a9057bcd619534a49f669dd5ed3078",
            "testdir/c/d": "input-fdb1b8414eeab993acc5623371c43a71"
        },
        "mkdir -p testdir/c/g": {
            "testdir": "input-3ca0a3620b59afb57cf5fd77cee6432c",
            "testdir/c": "input-54a9057bcd619534a49f669dd5ed3078",
            "testdir/c/g": "output-c512be1476c9253326e479827c491f7f"
        },
        "mkdir testdir": {
            "testdir": "output-3ca0a3620b59afb57cf5fd77cee6432c"
        },
        "mkdir testdir/a": {
            "testdir/a": "output-832651e32363cb4b115b074240cd08b5"
        },
        "mkdir testdir/b": {
            "testdir/b": "output-0432d5c3dc41495725df46eeeedb1386"
        },
        "mkdir testdir/c": {
            "testdir/c": "output-54a9057bcd619534a49f669dd5ed3078"
        },
        "mkdir testdir/c/d": {
            "testdir/c/d": "output-fdb1b8414eeab993acc5623371c43a71"
        },
        "mkdir testdir/c/e": {
            "testdir/c/e": "output-eadea986453292aaa62ccde2312c3413"
        },
        "mkdir testdir/c/f": {
            "testdir/c/f": "output-5d7c7f98e6d795bbb252f6866c8d7850"
        },
        "touch testdir/b/f1": {
            "testdir/b/f1": "output-d41d8cd98f00b204e9800998ecf8427e"
        },
        "touch testdir/b/f2": {
            "testdir/b/f2": "output-d41d8cd98f00b204e9800998ecf8427e"
        },
        "touch testdir/c/d/f1": {
            "testdir/c/d/f1": "output-d41d8cd98f00b204e9800998ecf8427e"
        },
        "touch testdir/c/d/f2": {
            "testdir/c/d/f2": "output-d41d8cd98f00b204e9800998ecf8427e"
        },
        "touch testdir/f1": {
            "testdir/f1": "output-d41d8cd98f00b204e9800998ecf8427e"
        },
        "touch testdir/f2": {
            "testdir/f2": "output-d41d8cd98f00b204e9800998ecf8427e"
        }
    }

    # assertions
    with local.cwd(builddir):
        assert_json_equality('.deps', expected_json)
        assert os.path.isdir('testdir/c/g')
        assert os.path.isfile('testdir/c/d/f2')
        assert os.path.isdir('existingdir/a')
        sys.exit.assert_called_once_with(0)

    main(globals_dict=fabricate_file(),
         #parallel_ok=True,
         #jobs=4,
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'clean'])
    end_fabricate()

    with local.cwd(builddir):
        assert not os.path.isdir('testdir')
        assert os.path.isdir('existingdir')
        assert os.path.isfile('existingdir/existingfile')
        assert not os.path.isdir('existingdir/a')



# Builder.done compute the hash after the file has been removed !
# Thus dependency is lost, and the mv command is not applied when originalfile
# is changed
@pytest.mark.xfail
@pytest.mark.parametrize("runner", runner_list)
def test_rename(builddir, runner, end_fabricate):

    # build.py content >>>>>>>>>>>>>>>>>>>>>
    def fabricate_file():
        def build():
            run('mv', 'originalfile', 'testfile')

        def clean():
            autoclean()
            # remake the original file
            shell('touch', 'originalfile')

        return copy(locals())

    with local.cwd(builddir):
        sh.touch('originalfile')

    ###### First build ##########
    main(globals_dict=fabricate_file(),
         #parallel_ok=True,
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'build'])
    end_fabricate()

    expected_json = {
            ".deps_version": 2,
            "mv originalfile testfile": {
                "originalfile": "input-d41d8cd98f00b204e9800998ecf8427e",
                "testfile": "output-d41d8cd98f00b204e9800998ecf8427e"
            }
        }

    # assertions
    with local.cwd(builddir):
        assert_json_equality('.deps', expected_json)
        assert os.path.isfile('testfile')
        sys.exit.assert_called_once_with(0)

        # update original file to check the rebuild
        (sh.echo["newline"] > "originalfile")()

    ###### Second build ##########
    main(globals_dict=fabricate_file(),
         #parallel_ok=True,
         #jobs=4,
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'build'])
    end_fabricate()

    expected_json = {
            ".deps_version": 2,
            "mv originalfile testfile": {
                "originalfile": "input-321060ae067e2a25091be3372719e053",
                "testfile": "output-321060ae067e2a25091be3372719e053"
            }
        }

    with local.cwd(builddir):
        assert_json_equality('.deps', expected_json)
        assert "newline" in sh.cat('testfile')


    ###### Cleaning ##########
    main(globals_dict=fabricate_file(),
         #parallel_ok=True,
         #jobs=4,
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'clean'])
    end_fabricate()

    with local.cwd(builddir):
        assert not os.isfile('testfile')
        assert os.isfile('originalfile')

@pytest.mark.parametrize("runner", runner_list)
def test_symlink(builddir, runner, end_fabricate):

    # build.py content >>>>>>>>>>>>>>>>>>>>>
    def fabricate_file():
        def build():
            run('ln', '-s', 'testfile', 'testlink')
            run('ln', '-s', 'testdir', 'testlink_dir')
            run('ln', '-s', 'nofile', 'testlink_nofile')

        def clean():
            autoclean()

        return copy(locals())

    with local.cwd(builddir):
        sh.touch('testfile')
        sh.mkdir('testdir')

    ###### First build ##########
    main(globals_dict=fabricate_file(),
         #parallel_ok=True,
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'build'])
    end_fabricate()

    expected_json = {
        ".deps_version": 2,
        "ln -s nofile testlink_nofile": {
            "testlink_nofile": "output-"
        },
        "ln -s testdir testlink_dir": {
            "testlink_dir": "output-"
        },
        "ln -s testfile testlink": {
            "testlink": "output-"
        }
    }

    # assertions
    with local.cwd(builddir):
        assert_same_json('.deps', expected_json)
        assert os.path.islink('testlink')
        assert os.path.realpath('testlink').endswith('/testfile')
        assert os.path.islink('testlink_dir')
        assert os.path.realpath('testlink_dir').endswith('/testdir')
        assert os.path.islink('testlink_nofile')
        assert not os.path.isfile('testlink_nofile')
        sys.exit.assert_called_once_with(0)

    ###### Cleaning ##########
    main(globals_dict=fabricate_file(),
         #parallel_ok=True,
         #jobs=4,
         build_dir=builddir,
         runner=runner,
         command_line=['-D', 'clean'])
    end_fabricate()

    with local.cwd(builddir):
        assert not os.path.isfile('.deps')
        assert not os.path.islink('testlink')
        assert not os.path.islink('testlink_dir')
        assert not os.path.islink('testlink_nofile')

def test_md5_hasher(builddir):
    with local.cwd(builddir):
        sh.touch('testfile')
        sh.mkdir('testdir')
        sh.touch('testdir/testfile')
        sh.ln('-s', 'testdir', 'testdirlink')
        sh.ln('-s', 'testfile', 'testlink')
        sh.ln('-s', 'nofile', 'testlink_nofile')
        assert md5_hasher('nofile') == None
        assert md5_hasher('testfile') == EMPY_FILE_MD5
        assert md5_hasher('testdir') == md5func('testdir').hexdigest()
        assert md5_hasher('testlink') == EMPY_FILE_MD5
        assert md5_hasher('testdirlink') == md5func('testdir').hexdigest()
        assert md5_hasher('testlink_nofile') == md5func('nofile').hexdigest()


