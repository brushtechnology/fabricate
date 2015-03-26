# Running Commands in Parallel #

Normally fabricate runs the commands you specify in sequence
in the order they are specified.  This is simple and easy to
understand.

However build performance can be improved by running more than one
command at once.  This can take advantage of multiple cores and
even on a single core processor can improve performance by keeping
the CPU busy whilst it is waiting for the disk.

There are two parts to telling fabricate to run commands in parallel,

  1. Telling it that it is safe to build in parallel
  1. Telling it which commands to run in parallel

Skip [straight to examples](http://code.google.com/p/fabricate/wiki/ParallelBuilding#Examples).

# Parallel Usage #

The user script must use fabricate slightly differently for parallel operation as follows:

## main() ##

The Builder class constructor and so main() now takes the boolean keyword
option 'parallel\_ok'.  Set to True this indicates to fabricate that the
script has been set up to be safe to run in parallel.

Main() takes the integer keyword option 'jobs' that specifies the default
number of parallel jobs to run.  This can be overridden by the -j command
line option.  The resultant value must be greater than one to run commands in
parallel.

Parallel operation is only possible with StraceRunner.

If these three conditions are true then fabricate will run commands in
parallel, this will be known as 'parallel mode'.

## run() ##

run() still accepts any number of string arguments which become the
arguments to a single command to be run, but it also now accepts a single
iterable argument specifying many commands at once.  Each element is an
iterable of strings specifying a command and arguments.

When not in parallel mode, run() waits for the command or commands to finish
and returns the results or a list of results. Results are still a tuple
(command, deps, output).

If in parallel mode the commands in the iterable are presumed to be allowed
to run in parallel and run() will not wait for their completion. Nor will
run() wait for completion of a single command when in parallel mode.

It is often the case that a number of commands can run in  parallel but then
the next command has to wait until all the previous ones have finished, eg a
link has to wait for all the compiles to finish.

Setting the 'after' keyword parameter to True will prevent the command (or
list of commands) from being started until all commands from previous calls
to run() have completed.

Sometimes a command only needs to run after for some of the preceding
commands have completed, so there needs to be a way of grouping commands
together, and then commands can be run after the whole group have all
completed. The 'group' keyword parameter identifies the command(s) with a
group.  The 'group' parameter can be any hashable type except boolean (True
is used as the default for calls to run() without a group parameter and
False is used internally), it can be an integer, a string etc and is simply
an identifier for the group.

The 'after' parameter can take a group identifier or an iterable of
identifiers and the command(s) will not start until all commands identified
with these group(s) have completed.  Note that run() does not wait for this
to have happened.

In parallel mode run() does not wait for results, so it returns None.

## after() ##

There is a new function after() which takes the same parameters as the
'after' parameter to the run() function (defaults to True which will wait for
all).  The after() function will stop the whole script until the specified
groups have completed and will return their results as a list of tuples,
(group id, list of results in order of the calls to run()).

Results are only returned for commands that actually need to be run because
of changes in their dependencies. Groups may be missing if no commands
associated with them were run.

Commands scheduled by calls to run() without specifying a group will default
to a group id of True.

## Error handling ##

When not running in parallel mode there is no change to the current behavior
when a command returns a non-zero status.

When running in parallel mode exceptions are not propogated, instead the
exception object is returned instead of the command results tuple.

When an command error has occurred in parallel mode, no command will run
which is scheduled 'after' the group identified with the failed command.
Other commands will continue to be scheduled and run.

# Examples #

Based on the following non-parallel script:

```
from fabricate import *

library_sources = ['lib/source1', 'lib/source2']
main_sources = ['src/main', 'src/other']

def build():
    compile()
    link()

def compile():
    for source in library_sources:
        run('gcc', '-c', source+'.c')
    for source in main_sources:
        run('g++', '-c', source+'.cxx')

def link():
    objects = [s+'.o' for s in library_sources]
    run('ar', 'T', 'lib/library.a', objects)
    objects = [s+'.o' for s in main_sources]
    run('gcc', '-o', 'program', objects, 'lib/library.a')
    
main()
```

The next script does all the compiles in parallel then does the links one after
the other after all the compiles are finished (note the use of after() to do
this).

```
from fabricate import *

library_sources = ['lib/source1', 'lib/source2']
main_sources = ['src/main', 'src/other']

def build():
    compile()
    link()

def compile():
    for source in library_sources:
        run('gcc', '-c', source+'.c')
    for source in main_sources:
        run('g++', '-c', source+'.cxx')

def link():
    objects = [s+'.o' for s in library_sources]
    after(); run('ar', 'T', 'lib/library.a', objects)
    objects = [s+'.o' for s in main_sources]
    after(); run('gcc', '-o', 'program', objects, 'lib/library.a')

main(parallel_ok=True, jobs=3)
```

The next script makes the links depend only on the specific compiles that
are relevant using 'group' and 'after' parameters (note the archive command
could be part of the 'main' group so the link will wait on it, but its given
its own group for example purposes)

```
from fabricate import *

library_sources = ['lib/source1', 'lib/source2']
main_sources = ['src/main', 'src/other']

def build():
    compile()
    link()

def compile():
    for source in library_sources:
        run('gcc', '-c', source+'.c', group='lib')
    for source in main_sources:
        run('g++', '-c', source+'.cxx', group='main')

def link():
    objects = [s+'.o' for s in library_sources]
    run('ar', 'T', 'lib/library.a', objects, group='arch', after='lib')
    objects = [s+'.o' for s in main_sources]
    run('gcc', '-o', 'program', objects, 'lib/library.a', after=('main', 'arch'))

main(parallel_ok=True, jobs=3)
```