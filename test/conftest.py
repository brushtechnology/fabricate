import sys
import pytest
import os
import shutil
import atexit
import json
import inspect
import tempfile

sys.path.append('.')

from fabricate import *
import fabricate

from _pytest.monkeypatch import MonkeyPatch


__all__ = [ 'runner_list', 'assert_same_json', 'assert_json_equality', 'FabricateBuild']

possible_runner_list = [StraceRunner, AtimesRunner]
runner_list = []
temp_dir = tempfile.mkdtemp()
for r in possible_runner_list:
    try:
        if r(fabricate.Builder(dirs=[temp_dir])):
            runner_list.append(r)
    except fabricate.RunnerUnsupportedException:
        runner_list.append(pytest.param(r, marks=pytest.mark.skip))

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)

@pytest.fixture(autouse=True)
def mock_env(request, mocker):
    mocker.patch('sys.exit'
                 )  # prevent sys.exit from existing so as to do other tests

@pytest.fixture
def cleandir():
    """ Should the build directory be cleaned at the end of each test """
    return True


@pytest.fixture
def builddir(request, cleandir):
    bdir = os.path.join("build_dir", "%s-%s" % (request.module.__name__,
                                                request.function.__name__))
    try:
        shutil.rmtree(bdir)
    except OSError:
        pass
    os.makedirs(bdir)

    def fin():
        if cleandir:
            shutil.rmtree(bdir, ignore_errors=True)

    request.addfinalizer(fin)
    return bdir


def assert_same_json(depfile, depref):
    """ Are the json in '.deps' `depfile` and the dict in `depref` equivalent
    modulo the md5sum values """
    assert_json_equality(depfile, depref, structural_only=True)

def assert_json_equality(depfile, depref, structural_only=False):
    """ Are the json in '.deps' `depfile` and the dict in `depref` equivalent """
    def _replace_md5(d):
        for k in d:
            if isinstance(d[k], dict):
                _replace_md5(d[k])
            else:
                if isinstance(d[k], string_types):
                    if d[k].startswith("input-"):
                        d[k] = d[k][:6]
                    elif d[k].startswith("output-"):
                        d[k] = d[k][:7]
    with open(depfile, 'r') as depfd:
        out = json.load(depfd)
    if structural_only:
        _replace_md5(out)
        _replace_md5(depref)
    assert out == depref


class FabricateBuild(object):
    """
    Simple wrapper class for builds during testing
    """
    EXCLUDED_NAMES = set(['to_dict', 'main', 'EXCLUDED_NAMES', '_main_kwargs'])

    def __init__(self, **kwargs):
        """
        Any kwargs passed will be passed to fabricate.main when a call to .main is made
        """
        self._main_kwargs = kwargs

    def build(self):
        pass

    def clean(self):
        pass

    def main(self, *args, **kwargs):
        """execute the fabricate.main function with default
           kwargs as given to __init__ and
           globals_dict=self.to_dict()
        """

        kwargs['globals_dict'] = kwargs.pop('globals_dict', self.to_dict())

        for name in self._main_kwargs:
            kwargs[name] = kwargs.pop(name, self._main_kwargs[name])

        # --- intercept any exit atexit functions
        exithandlers = []
        def atexit_register(func, *targs, **kargs):
            exithandlers.append((func, targs, kargs))
            return func

        def run_exitfuncs():
            exc_info = None
            while exithandlers:
                func, targs, kargs = exithandlers.pop()
                try:
                    func(*targs, **kargs)
                except SystemExit:
                    exc_info = sys.exc_info()
                except:
                    import traceback
                    print >> sys.stderr, "Error in mock_env.run_exitfuncs:"
                    traceback.print_exc()
                    exc_info = sys.exc_info()

            if exc_info is not None:
                raise (exc_info[0], exc_info[1], exc_info[2])

        monkeypatch = MonkeyPatch()
        monkeypatch.setattr(atexit, 'register', atexit_register)

        try:
            fabricate.main(*args, **kwargs)
            run_exitfuncs()
        finally:
            monkeypatch.undo()


    def to_dict(self):
        dct = {}

        # filter out special names
        for name in dir(self):
            if name.startswith('__'):
                continue

            if name in self.EXCLUDED_NAMES:
                continue

            dct[name] = getattr(self, name)

        return dct
