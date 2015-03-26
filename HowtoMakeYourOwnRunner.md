## How to create your own `runner` class ##

If you'd like to find dependencies another way (not strace or atimes), or if you'd like to customise the Builder for some other reason, you can easily subclass `fabricate.Runner`.

For example, one way to find dependencies using gcc's -M options (instead of strace or atimes) would be to subclass `Runner` as shown below. Simply implement a `__call__()` function to do the work of running commands and finding dependencies and outputs.

**Note: this is just an example of creating your own `runner`, not our recommendation. In most cases you can use the default Runner just fine.**

```
import os
import sys
from fabricate import *

class GccRunner(Runner):
    """ Runner subclass example that uses gcc's -M dependency generation if it
        can, otherwise defaults to the default "smart" dependency runner. """

    def __init__(self, builder):
        self.smart_runner = SmartRunner(builder)    # get runner instance

    def __call__(self, *args):
        """ Run command using gcc dependency generation if it looks possible,
            otherwise use the default smart runner to find dependencies. """
        if self.is_gcc(args):
            return self.gcc_runner(args)
        else:
            return self.smart_runner(args)

    def is_gcc(self, args):
        """ Return True if command looks like a gcc command. """
        return args[0].endswith('gcc') or args[0].endswith('gcc.exe')

    def gcc_runner(self, args):
        """ Run gcc command and return its dependencies and outputs. """
        if '-c' in args:
            return self.gcc_compile_runner(args)
        else:
            return self.gcc_link_runner(args)

    def gcc_compile_runner(self, args):
        """ Run gcc compile command and return its list of dependencies and
            outputs, using gcc's -M options to determine dependencies. """
        deps_file = 'temp.d'
        args = list(args) + ['-MMD', '-MF', deps_file]
        shell(args, silent=False)
        f = open(deps_file)
        try:
            target, deps_data = f.read().split(':', 1)
        finally:
            f.close()
        os.remove(deps_file)
        deps = []
        for line in deps_data.split('\n'):
            if line.endswith(' \\'):
                line = line[:-2]
            # temporarily replace spaces in filenames with a char that will
            # "never" occur
            line = line.replace('\\ ', '#')
            for dep in line.split():
                dep = dep.replace('#', ' ')
                deps.append(os.path.abspath(dep))
        outputs = [os.path.abspath(target)]
        return deps, outputs

    def gcc_link_runner(self, args):
        """ Run gcc link command and return its list of dependencies and
            outputs, using given gcc command to determine dependencies. """
        target = args[list(args).index('-o') + 1]
        if sys.platform == 'win32' and not target.endswith('.exe'):
            target += '.exe'
        deps = [os.path.abspath(a) for a in args if a.endswith('.o')]
        shell(args, silent=False)
        outputs = [os.path.abspath(target)]
        return deps, outputs

# set up fabricate to use GccRunner
setup(runner=GccRunner)

# ... rest of your build script here, as normal ...
```