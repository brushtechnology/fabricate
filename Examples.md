## Examples of fabricate build scripts ##

Most of these examples assume you've got a main program with source in `program.c` and an associated `util.c`, both of which include `util.h`. The final output is a `program` executable (`program.exe` on Windows).

### Simplest ###

Below is the simplest, albeit least flexible, example of a build script for this program. It's not recommended because it's hard to maintain as you add source files and other options.

```
from fabricate import *
run('gcc', '-c', 'program.c')
run('gcc', '-c', 'util.c')
run('gcc', '-o', 'program', 'program.o', 'util.o')
```

### Recommended ###

This example (same as the one on the [project home page](http://code.google.com/p/fabricate/) is the "recommended" way to set up your fabricate build scripts. This way allows you to simply specify a list of sources, as in `sources = ['program', 'util']`. It also gives you an autoclean "target", which you execute via `build.py clean`.

```
from fabricate import *

sources = ['program', 'util']

def build():
    compile()
    link()

def compile():
    for source in sources:
        run('gcc', '-c', source+'.c')

def link():
    objects = [s+'.o' for s in sources]
    run('gcc', '-o', 'program', objects)

def clean():
    autoclean()

main()
```

### Different build and source directories ###

This one adds some features and gets a bit more complicated. It assumes `util.c` and `util.h` are in another directory, `../lib`, and it has two different build targets: `build` and `profile`, which build into the `build/` and `profile/` directories, respectively.

The `version()` function uses fabricate's `shell()` function to find the SVN revision, and writes that to a file called `version.h`. It also shows how to use fabricate's `setup()` function.

```
import os
from fabricate import *

setup(dirs=['.', '../lib'])

target = 'program'
sources = ['program', '../lib/util']
cflags = '-Wall -O2'.split()

def build():
    version()
    compile()
    link()

def version():
    revision = shell('svnversion').strip()
    print >>file('version.h', 'w'), '#define REVISION "%s"' % revision

def oname(build_dir, filename):
    return os.path.join(build_dir, os.path.basename(filename))

def compile(build_dir='build', flags=None):
    for source in sources:
        run('gcc', '-c', source+'.c', '-o', oname(build_dir, source+'.o'), cflags, flags)

def link(build_dir='build', flags=None):
    objects = [oname(build_dir, s+'.o') for s in sources]
    run('gcc', objects, '-o', oname(build_dir, target), flags)

def profile():
    version()
    compile('profile', flags=['-pg'])
    link('profile', flags=['-pg'])

def check():
    return int(outofdate(build))

def clean():
    autoclean()

def rebuild():
    clean()
    build()

main()
```