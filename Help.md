As with any Python program, you can get help right from within Python:
```
# python
>>> import fabricate
>>> help(fabricate)
>>> help(fabricate.<specific_function>)
```

This will show some very detailed help, but you'll notice near the top a list of exported functions that you can get help on.  This list includes all exported functions, but with the most essential ones first: setup, run, main, autoclean, fabricate\_version, etc.

For example:

```
>>> help(fabricate.run)
Help on function run in module fabricate:

run(*args)
    Run the given command, but only if its dependencies have changed. Uses
    the default Builder.
```

Alternatively, if you import fabricate the recommended way for build scripts, you can get help on specific functions like this:
```
# python
>>> from fabricate import *
>>> help(<function>)
```

If this doesn't get you anywhere, search for the specific function you want inside the source.  It's simple source and the chances are that even if you don't know Python, you'll be able to figure out basically what you need to know.