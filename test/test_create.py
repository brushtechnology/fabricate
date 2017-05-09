import sys
import pytest
import plumbum.cmd as sh
from plumbum import local
import os

from fabricate import *
from conftest import *

class BuildFile(FabricateBuild):

    def build(self):
        run('tar', 'czvf', 'foo.tar.gz', 'a.c', 'b.c')

    def clean(self):
        autoclean()


@pytest.mark.parametrize("runner", runner_list)
def test_create(builddir, runner):
    # prepare needed files
    with local.cwd(builddir):
        (sh.echo["a.c"] > "a.c")()
        (sh.echo["b.c"] > "b.c")()

    builder = BuildFile(build_dir=builddir, runner=runner)
    builder.main(command_line=['-c', '-D', 'build'])

    expected_json = {
        'tar czvf foo.tar.gz a.c b.c': {
            'b.c': 'input-',
            'foo.tar.gz': 'output-',
            'a.c': 'input-'
        },
        '.deps_version': 2
    }

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

    builder.main(command_line=['-D', 'build'])

    with local.cwd(builddir):
        sh.tar("df", "foo.tar.gz") # ensure tar diff return no difference
