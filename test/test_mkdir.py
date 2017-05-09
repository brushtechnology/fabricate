import sys
import pytest
import plumbum.cmd as sh
from plumbum import local
import os

from fabricate import *
from conftest import *

class BuildFile(FabricateBuild):
    def build(self):
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

    def clean(self):
        autoclean()


@pytest.mark.parametrize("runner", runner_list)
def test_mkdir(builddir, runner):
    # prepare needed files
    with local.cwd(builddir):
        sh.mkdir('existingdir')
        sh.touch('existingdir/existingfile')

    builder = BuildFile(build_dir=builddir, runner=runner)
    builder.main(command_line=['-D', 'build']) #, parallel_ok=True)

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

    builder.main(command_line=['-D', 'clean']) 
    #parallel_ok=True,
    #jobs=4,

    with local.cwd(builddir):
        assert not os.path.isdir('testdir')
        assert os.path.isdir('existingdir')
        assert os.path.isfile('existingdir/existingfile')
        assert not os.path.isdir('existingdir/a')


