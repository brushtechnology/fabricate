
fabricate is a build tool that finds dependencies automatically for any language. It's small and just works. No hidden stuff behind your back. It was inspired by Bill McCloskey's make replacement, memoize, but fabricate works on Windows as well as Linux.

Get fabricate.py now, learn how it works, see how to get in-Python help, or discuss it on the mailing list.

Features
* Never have to list dependencies.
* Never have to specify cleanup rules.
* The tool is a single Python file.
* It uses MD5 (not timestamps) to check inputs and outputs.
* You can learn it all in about 10 minutes.
* You can still read your build scripts 3 months later.
* Now supports parallel building

Show me an example!

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

This isn't the simplest build script you can make with fabricate (see other examples), but it's surprisingly close to some of the more complex scripts we use in real life. Things to note:

* It's an ordinary Python file. Use the clarity and power of Python.
* No implicit stuff like CCFLAGS.
* Explicit is better: you tell fabricate what commands to run, and it runs them -- but only if their inputs or outputs have changed.
* Where you'd use targets in make, you just use Python functions -- build() is the default.
* You can easily "autoclean" any build outputs -- fabricate finds build outputs automatically, just like it finds dependencies.

Using fabricate options
-----------------------

The best way to get started is to take one of the examples linked above and modify it to suit your project. But you're bound to want to use some of the options built into fabricate. To get a list of these:

	 from fabricate import *

	 help(main)
	 help(Builder)

Using fabricate as a script, a la memoize
-----------------------------------------

You can also use fabricate.py as a script and enter commands directly on the command line (see command line options). In the following, each gcc command will only be run if its dependencies have changed:

	fabricate.py gcc -c program.c
	fabricate.py gcc -c util.c
	fabricate.py gcc -o program program.o util.o

Why not use make?
-----------------

For a start, fabricate won't say "missing separator" if you use spaces instead of tabs. And you'll never need to enter dependencies manually, like this:

	files.o : files.c defs.h buffer.h command.h
	        cc -c files.c

Instead, you just tell fabricate to run('cc', 'file.c') and it'll figure out what that command's inputs and outputs are. Next time you build, the command will only get run if its inputs have changed, or if its outputs have been modified or aren't there.

And you can use Python's readable string functions instead of producing write-only make rules, like this one from the make docs:

	%.d : %.c
	        @set -e; rm -f $@; $(CC) -M $(CPPFLAGS) $< > $@.$$$$; \
	        sed 's,\($*\)\.o[ :]*,\1.o $@ : ,g' < $@.$$$$ > $@; rm -f $@.$$$$

What about SCons?
-----------------

SCons tempted us at first too. It's Python ... isn't it? But just before it sucks you in, you realise it's actually quite hard to do simple things explicitly.

Python says that explicit is better than implicit for a reason, and with fabricate, we've made it so you tell it what you want. It won't do things behind your back based on the 83 different tools it may or may not know about.

Credits
-------
fabricate is inspired by Bill McCloskey's memoize, but fabricate works under Windows as well by using file access times instead of strace if strace is not available on your file system. Read more about how fabricate works.

fabricate was developed by the B Hoyts at Brush Technology for in-house use, but they thought it was cool enough to release into the wild. It lived on google code for awhile, then pjz moved it from svn there to git on github.

