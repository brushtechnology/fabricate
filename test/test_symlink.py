import sys
import pytest
import plumbum.cmd as sh
from plumbum import local
import os

from fabricate import *
from conftest import *

class BuildFile(FabricateBuild):
    def build(self):
        run('ln', '-s', 'testfile', 'testlink')
        run('ln', '-s', 'testdir', 'testlink_dir')
        run('ln', '-s', 'nofile', 'testlink_nofile')

    def clean(self):
        autoclean()

@pytest.mark.parametrize("runner", runner_list)
def test_symlink(builddir, runner):
    builder = BuildFile(build_dir=builddir, runner=runner)

    with local.cwd(builddir):
        sh.touch('testfile')
        sh.mkdir('testdir')

    ###### First build ##########
    builder.main(command_line=['-D', 'build'])

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
    builder.main(command_line=['-D', 'clean'])

    with local.cwd(builddir):
        assert not os.path.isfile('.deps')
        assert not os.path.islink('testlink')
        assert not os.path.islink('testlink_dir')
        assert not os.path.islink('testlink_nofile')

