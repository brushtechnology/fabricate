import sys
import pytest
import plumbum.cmd as sh
from plumbum import local
import os

from fabricate import *
from conftest import *


class BuildFile(FabricateBuild):
    def build(self):
        run('mv', 'originalfile', 'testfile')

    def clean(self):
        autoclean()
        # remake the original file
        shell('touch', 'originalfile')


# Builder.done compute the hash after the file has been removed !
# Thus dependency is lost, and the mv command is not applied when originalfile
# is changed
@pytest.mark.xfail
@pytest.mark.parametrize("runner", runner_list)
def test_rename(builddir, runner):
    # prepare needed files
    with local.cwd(builddir):
        sh.touch('originalfile')

    builder = BuildFile(build_dir=builddir, runner=runner)

    ###### First build ##########
    builder.main(command_line=['-D', 'build'])

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
    builder.main(command_line=['-D', 'build'])

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
    builder.main(command_line=['-D', 'clean'])

    with local.cwd(builddir):
        assert not os.isfile('testfile')
        assert os.isfile('originalfile')
