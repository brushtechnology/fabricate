import sys
import pytest
import os
import shutil
import atexit
import json
sys.path.append('.')
from fabricate import *

__all__ = [ 'runner_list', 'assert_same_json', 'assert_json_equality']

runner_list = [StraceRunner, AtimesRunner]

@pytest.fixture(autouse=True)
def mock_env(request, mocker):
    mocker.patch('sys.exit'
                 )  # prevent sys.exit from existing so as to do other tests


@pytest.fixture()
def end_fabricate(request, monkeypatch):
    """ This fixture replace atexit.register with its own local implementation
    in order to allow one test to be fully executed (including atexit registred
    functions) """
    exithandlers = []

    def testexit_register(func, *targs, **kargs):
        exithandlers.append((func, targs, kargs))
        return func

    monkeypatch.setattr(atexit, 'register', testexit_register)

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
            raise exc_info[0], exc_info[1], exc_info[2]

    return run_exitfuncs


@pytest.fixture
def cleandir():
    """ Sould the build directory be cleaned at the end of each test """
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
                if isinstance(d[k], basestring):
                    if d[k].startswith("input-"):
                        d[k] = d[k][:6]
                    elif d[k].startswith("output-"):
                        d[k] = d[k][:7]
    with open(depfile, 'r') as  depfd:
        out = json.load(depfd)
    if structural_only:
        _replace_md5(out)
        _replace_md5(depref)
    assert out == depref

