""" Build tool that finds dependencies automatically for any language.

fabricate is a build tool that finds dependencies automatically for any
language. It's small and just works. No hidden stuff behind your back. It was
inspired by Bill McCloskey's make replacement, memoize, but fabricate works on
Windows as well as Linux.

Read more about how to use it and how it works on the project page:
    http://code.google.com/p/fabricate/

Like memoize, fabricate is released under a "New BSD license". fabricate is
copyright (c) 2009 Brush Technology. Full text of the license is here:
    http://code.google.com/p/fabricate/wiki/License

"""

# so you can do "from fabricate import *" to simplify your build script
__all__ = ['ExecutionError', 'shell', 'md5_hasher', 'mtime_hasher',
           'Runner', 'AtimesRunner', 'StraceRunner', 'Builder',
           'setup', 'run', 'autoclean', 'memoize', 'outofdate', 'main']

# fabricate version number
__version__ = '1.08'

# if version of .deps file has changed, we know to not use it
deps_version = 1

import atexit
import optparse
import os
import platform
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import time

FAT_atime_resolution = 24*60*60     # resolution on FAT filesystems (seconds)
FAT_mtime_resolution = 2

# NTFS resolution is < 1 ms
#  We assume this is considerably more than time to run a new process

NTFS_atime_resolution = 0.0002048   # resolution on NTFS filesystems (seconds)
NTFS_mtime_resolution = 0.0002048   #  is actually 0.1us but python's can be
                                    #  as low as 204.8us due to poor
                                    #  float precision when storing numbers
                                    #  as big as NTFS file times can be
                                    #  (float has 52-bit precision and NTFS
                                    #  FILETIME has 63-bit precision, so
                                    #  we've lost 11 bits = 2048)

# So we can use md5func in old and new versions of Python without warnings
try:
    import hashlib
    md5func = hashlib.md5
except ImportError:
    import md5
    md5func = md5.new

# Use json, or pickle on older Python versions if simplejson not installed
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import cPickle
        # needed to ignore the indent= argument for pickle's dump()
        class PickleJson:
            def load(self, f):
                return cPickle.load(f)
            def dump(self, obj, f, indent=None, sort_keys=None):
                return cPickle.dump(obj, f)
        json = PickleJson()

def printerr(message):
    """ Print given message to stderr with a line feed. """
    print >>sys.stderr, message

class ExecutionError(Exception):
    """ Raised by shell() and run() if command returns non-zero exit code. """
    pass

def args_to_list(args):
    """ Return a flat list of the given arguments for shell(). """
    arglist = []
    for arg in args:
        if arg is None:
            continue
        if hasattr(arg, '__iter__'):
            arglist.extend(args_to_list(arg))
        else:
            if not isinstance(arg, basestring):
                arg = str(arg)
            arglist.append(arg)
    return arglist

def shell(*args, **kwargs):
    r""" Run a command: program name is given in first arg and command line
        arguments in the rest of the args. Iterables (lists and tuples) in args
        are recursively converted to separate arguments, non-string types are
        converted with str(arg), and None is ignored. For example:

        >>> def tail(input, n=3, flags=None):
        >>>     args = ['-n', n]
        >>>     return shell('tail', args, flags, input=input)
        >>> tail('a\nb\nc\nd\ne\n')
        'c\nd\ne\n'
        >>> tail('a\nb\nc\nd\ne\n', 2, ['-v'])
        '==> standard input <==\nd\ne\n'

        Keyword arguments kwargs are interpreted as follows:

        "input" is a string to pass standard input into the process (or the
            default of None to use parent's stdin, eg: the keyboard)
        "silent" is True (default) to return process's standard output as a
            string, or False to print it as it comes out
        "shell" set to True will run the command via the shell (/bin/sh or
            COMSPEC) instead of running the command directly (the default)

        Raises ExecutionError(message, output, status) if the command returns
        a non-zero status code. """
    return _shell(args, **kwargs)

def _shell(args, input=None, silent=True, shell=False):
    if input:
        stdin = subprocess.PIPE
    else:
        stdin = None
    if silent:
        stdout = subprocess.PIPE
    else:
        stdout = None
    arglist = args_to_list(args)
    if not arglist:
        raise TypeError('shell() takes at least 1 argument (0 given)')
    if shell:
        # handle subprocess.Popen quirk where subsequent args are passed
        # to bash instead of to our command
        command = subprocess.list2cmdline(arglist)
    else:
        command = arglist
    proc = subprocess.Popen(command, stdin=stdin, stdout=stdout,
                            stderr=subprocess.STDOUT, shell=shell)
    output, stderr = proc.communicate(input)
    status = proc.wait()
    if status:
        raise ExecutionError('%r exited with status %d'
                             % (os.path.basename(arglist[0]), status),
                             output, status)
    if silent:
        return output

def md5_hasher(filename):
    """ Return MD5 hash of given filename, or None if file doesn't exist. """
    try:
        f = open(filename, 'rb')
        try:
            return md5func(f.read()).hexdigest()
        finally:
            f.close()
    except IOError:
        return None

def mtime_hasher(filename):
    """ Return modification time of file, or None if file doesn't exist. """
    try:
        st = os.stat(filename)
        return repr(st.st_mtime)
    except (IOError, OSError):
        return None

def shrink_path(filename):
    """ Try to shrink a filename for display (remove the leading path if the
        file is relative to the current working directory). """
    cwd = os.getcwd()
    prefix = os.path.commonprefix([cwd, filename])
    if prefix:
        filename = filename[len(prefix)+1:]
    return filename

class Runner(object):
    def __init__(self, builder):
        self._builder = builder

    def __call__(self, *args):
        """ Run command and return (dependencies, outputs), where
            dependencies is a list of the filenames of files that the
            command depended on, and output is a list of the filenames
            of files that the command modified."""

        raise NotImplementedError()

class AtimesRunner(Runner):
    @staticmethod
    def file_has_atimes(filename):
        """ Return whether the given filesystem supports access time updates for
            this file. Return:
              - 0 if no a/mtimes not updated
              - 1 if the atime resolution is at least one day and
                the mtime resolution at least 2 seconds (as on FAT filesystems)
              - 2 if the atime and mtime resolutions are both < ms
                (NTFS filesystem has 100 ns resolution). """

        def access_file(filename):
            """ Access (read a byte from) file to try to update its access time. """
            f = open(filename)
            f.read(1)
            f.close()

        initial = os.stat(filename)
        os.utime(filename, (
            initial.st_atime-FAT_atime_resolution,
            initial.st_mtime-FAT_mtime_resolution))

        adjusted = os.stat(filename)
        access_file(filename)
        after = os.stat(filename)

        # Check that a/mtimes actually moved back by at least resolution and
        #  updated by a file access.
        #  add NTFS_atime_resolution to account for float resolution factors
        #  Comment on resolution/2 in atimes_runner()
        if initial.st_atime-adjusted.st_atime > FAT_atime_resolution+NTFS_atime_resolution or \
           initial.st_mtime-adjusted.st_mtime > FAT_mtime_resolution+NTFS_atime_resolution or \
           initial.st_atime==adjusted.st_atime or \
           initial.st_mtime==adjusted.st_mtime or \
           not after.st_atime-FAT_atime_resolution/2 > adjusted.st_atime:
            return 0

        os.utime(filename, (
            initial.st_atime-NTFS_atime_resolution,
            initial.st_mtime-NTFS_mtime_resolution))
        adjusted = os.stat(filename)

        # Check that a/mtimes actually moved back by at least resolution
        # Note: != comparison here fails due to float rounding error
        #  double NTFS_atime_resolution to account for float resolution factors
        if initial.st_atime-adjusted.st_atime > NTFS_atime_resolution*2 or \
           initial.st_mtime-adjusted.st_mtime > NTFS_mtime_resolution*2 or \
           initial.st_atime==adjusted.st_atime or \
           initial.st_mtime==adjusted.st_mtime:
            return 1

        return 2

    @staticmethod
    def has_atimes(paths):
        """ Return whether a file created in each path supports atimes and mtimes.
            Return value is the same as used by file_has_atimes
            Note: for speed, this only tests files created at the top directory
            of each path. A safe assumption in most build environments.
            In the unusual case that any sub-directories are mounted
            on alternate file systems that don't support atimes, the build may
            fail to identify a dependency """

        atimes = 2                  # start by assuming we have best atimes
        for path in paths:
            handle, filename = tempfile.mkstemp(dir=path)
            try:
                try:
                    f = os.fdopen(handle, 'wb')
                except:
                    os.close(handle)
                    raise
                try:
                    f.write('x')    # need a byte in the file for access test
                finally:
                    f.close()
                atimes = min(atimes, AtimesRunner.file_has_atimes(filename))
            finally:
                os.remove(filename)
        return atimes

    def _file_times(self, path, depth):
        """ Helper function for file_times().
            Return a dict of file times, recursing directories that don't
            start with self._builder.ignoreprefix """

        names = os.listdir(path)
        times = {}
        ignoreprefix = self._builder.ignoreprefix
        for name in names:
            if ignoreprefix and name.startswith(ignoreprefix):
                continue
            fullname = os.path.join(path, name)
            st = os.stat(fullname)
            if stat.S_ISDIR(st.st_mode):
                if depth > 1:
                    times.update(self._file_times(fullname, depth-1))
            elif stat.S_ISREG(st.st_mode):
                times[fullname] = st.st_atime, st.st_mtime
        return times

    def file_times(self):
        """ Return a dict of "filepath: (atime, mtime)" entries for each file
            in self._builder.dirs. "filepath" is the absolute path, "atime" is
            the access time, "mtime" the modification time.
            Recurse directories that don't start with
            self._builder.ignoreprefix and have depth less than
            self._builder.dirdepth. """

        times = {}
        for path in self._builder.dirs:
            times.update(self._file_times(os.path.abspath(path),
                                          self._builder.dirdepth))
        return times

    def _utime(self, filename, atime, mtime):
        """ Call os.utime but ignore permission errors """
        try:
            os.utime(filename, (atime, mtime))
        except OSError, e:
            # ignore permission errors -- we can't build with files
            # that we can't access anyway
            if e.errno != 1:
                raise

    def _age_atimes(self, filetimes):
        """ Age files' atimes and mtimes to be at least FAT_xx_resolution old.
            Only adjust if the given filetimes dict says it isn't that old,
            and return a new dict of filetimes with the ages adjusted. """
        adjusted = {}
        now = time.time()
        for filename, entry in filetimes.iteritems():
            if now-entry[0] < FAT_atime_resolution or now-entry[1] < FAT_mtime_resolution:
                entry = entry[0] - FAT_atime_resolution, entry[1] - FAT_mtime_resolution
                self._utime(filename, entry[0], entry[1])
            adjusted[filename] = entry
        return adjusted

    def __call__(self, *args):
        """ Run command and return its dependencies and outputs, using before
            and after access times to determine dependencies. """

        # For Python pre-2.5, ensure os.stat() returns float atimes
        old_stat_float = os.stat_float_times()
        os.stat_float_times(True)

        originals = self.file_times()
        if self._builder.atimes == 2:
            befores = originals
            atime_resolution = 0
            mtime_resolution = 0
        else:
            befores = self._age_atimes(originals)
            atime_resolution = FAT_atime_resolution
            mtime_resolution = FAT_mtime_resolution
        shell(*args, **dict(silent=False))
        afters = self.file_times()
        deps = []
        outputs = []
        for name in afters:
            if name in befores:
                # if file exists before+after && mtime changed, add to outputs
                # Note: Can't just check that atimes > than we think they were
                #       before because os might have rounded them to a later
                #       date than what we think we set them to in befores.
                #       So we make sure they're > by at least 1/2 the
                #       resolution.  This will work for anything with a
                #       resolution better than FAT.
                if afters[name][1]-mtime_resolution/2 > befores[name][1]:
                    outputs.append(name)
                elif afters[name][0]-atime_resolution/2 > befores[name][0]:
                    # otherwise add to deps if atime changed
                    deps.append(name)
            else:
                # file created (in afters but not befores), add as output
                outputs.append(name)

        if self._builder.atimes < 2:
            # Restore atimes of files we didn't access: not for any functional
            # reason -- it's just to preserve the access time for the user's info
            for name in deps:
                originals.pop(name)
            for name in originals:
                original = originals[name]
                if original != afters.get(name, None):
                    self._utime(name, original[0], original[1])

        os.stat_float_times(old_stat_float)  # restore stat_float_times value
        return deps, outputs

class StraceRunner(Runner):
    @staticmethod
    def has_strace():
        """ Return True if this system has strace. """
        if platform.system() == 'Windows':
            # even if windows has strace, it's probably a dodgy cygwin one
            return False
        try:
            subprocess.Popen('strace', stderr=subprocess.PIPE)
            return True
        except OSError:
            return False

    _open_re = re.compile(r'.*open\("([^"]*)", ([^,)]*)')
    _stat64_re = re.compile(r'.*stat64\("([^"]*)", .*')
    _execve_re = re.compile(r'.*execve\("([^"]*)", .*')
    _mkdir_re = re.compile(r'.*mkdir\("([^"]*)", .*')
    _rename_re = re.compile(r'.*rename\("[^"]*", "([^"]*)"\)')
    _kill_re = re.compile(r'.*killed by.*')
    _chdir_re = re.compile(r'.*chdir\("([^"]*)"\)')
    _exit_group_re = re.compile(r'.*exit_group\((.*)\).*')

    def _do_strace(self, args, outfile, outname):
        """ Run strace on given command args, sending output to file.
            Return (status code, list of dependencies, list of outputs). """
        shell('strace', '-fo', outname,
              '-e', 'trace=open,stat64,execve,exit_group,chdir,mkdir,rename',
              args, silent=False)

        cwd = os.getcwd()
        status = 0
        deps = set()
        outputs = set()
        for line in outfile:
            is_output = False
            open_match = self._open_re.match(line)
            stat64_match = self._stat64_re.match(line)
            execve_match = self._execve_re.match(line)
            mkdir_match = self._mkdir_re.match(line)
            rename_match = self._rename_re.match(line)

            kill_match = self._kill_re.match(line)
            if kill_match:
                return None, None, None

            match = None
            if open_match:
                match = open_match
                mode = match.group(2)
                if 'O_WRONLY' in mode or 'O_RDWR' in mode:
                    # it's an output file if opened for writing
                    is_output = True
            elif stat64_match:
                match = stat64_match
            elif execve_match:
                match = execve_match
            elif mkdir_match:
                match = mkdir_match
            elif rename_match:
                match = rename_match
                # the destination of a rename is an output file
                is_output = True
            if match:
                name = os.path.normpath(os.path.join(cwd, match.group(1)))
                if self._builder._is_relevant(name) \
                       and (os.path.isfile(name)
                            or os.path.isdir(name)
                            or not os.path.lexists(name)):
                    if is_output:
                        outputs.add(name)
                    else:
                        deps.add(name)

            match = self._chdir_re.match(line)
            if match:
                cwd = os.path.normpath(os.path.join(cwd, match.group(1)))

            match = self._exit_group_re.match(line)
            if match:
                status = int(match.group(1))

        return status, list(deps), list(outputs)

    def __call__(self, *args):
        """ Run command and return its dependencies and outputs, using strace
            to determine dependencies (by looking at what files are opened or
            modified). """
        handle, outname = tempfile.mkstemp()
        try:
            try:
                outfile = os.fdopen(handle, 'r')
            except:
                os.close(handle)
                raise
            try:
                status, deps, outputs = self._do_strace(args, outfile, outname)
                if status is None:
                    raise ExecutionError(
                        '%r was killed unexpectedly' % args[0], '', -1)
            finally:
                outfile.close()
        finally:
            os.remove(outname)

        if status:
            raise ExecutionError('%r exited with status %d'
                                 % (os.path.basename(args[0]), status),
                                 '', status)
        return list(deps), list(outputs)

class Builder(object):
    """ The Builder.

        You can subclass this and override the "runner" function to do what you
        want. For an example, see:
            http://code.google.com/p/fabricate/wiki/HowtoSubclassBuilder

        "runner" is the function used to run commands and generate
        dependencies. It must take a program name and a list of arguments, and
        return a tuple of (deps, outputs), where deps is a list of abspath'd
        dependency files and outputs a list of abspath'd output files. It
        defaults to a function that just calls smart_runner, which uses
        strace_runner or AtimesRunner as it can, automatically.
    """

    def __init__(self, runner=None, dirs=None, dirdepth=100, ignoreprefix='.',
                 hasher=md5_hasher, depsname='.deps', quiet=False):
        """ Initialise a Builder with the given options.

        "runner" specifies how programs should be run.  It is either a
            callable compatible with the Runner class, or a string selecting
            one of the standard runners ("atimes_runner", "strace_runner",
            "always_runner", or "smart_runner").
        "dirs" is a list of paths to look for dependencies (or outputs) in
            if using the strace or atimes runners.
        "dirdepth" is the depth to recurse into the paths in "dirs" (default
            essentially means infinitely). Set to 1 to just look at the
            immediate paths in "dirs" and not recurse at all. This can be
            useful to speed up the AtimesRunner if you're building in a large
            tree and you don't care about all of the subdirectories.
        "ignoreprefix" prevents recursion into directories that start with
            prefix.  It defaults to '.' to ignore svn directories.
            Change it to '_svn' if you use _svn hidden directories.
        "hasher" is a function which returns a string which changes when
            the contents of its filename argument changes, or None on error.
            Default is md5_hasher, but can also be mtime_hasher.
        "depsname" is the name of the JSON dependency file to load/save.
        "quiet" set to True tells the builder to not display the commands being
            executed (or other non-error output).
        """
        if runner is not None:
            self.set_runner(runner)
        if dirs is None:
            dirs = ['.']
        self.dirs = [os.path.abspath(path) for path in dirs]
        self.dirdepth = dirdepth
        self.ignoreprefix = ignoreprefix
        self.depsname = depsname
        self.hasher = hasher
        self.quiet = quiet
        self.checking = False

    def echo(self, message):
        """ Print message, but only if builder is not in quiet mode. """
        if not self.quiet:
            print message

    def echo_command(self, command):
        """ Show a command being executed. """
        self.echo(command)

    def echo_delete(self, filename, error=None):
        """ Show a file being deleted. For subclassing Builder and overriding
            this function, the exception is passed in if an OSError occurs
            while deleting a file. """
        if error is None:
            self.echo('deleting %s' % shrink_path(filename))

    def run(self, *args):
        """ Run command given in args as per shell(), but only if its
            dependencies or outputs have changed or don't exist. """
        arglist = args_to_list(args)
        if not arglist:
            raise TypeError('run() takes at least 1 argument (0 given)')
        # we want a command line string for the .deps file key and for display
        command = subprocess.list2cmdline(arglist)
        if not self.cmdline_outofdate(command):
            return

        # if just checking up-to-date-ness, set flag and do nothing more
        self.outofdate_flag = True
        if self.checking:
            return

        # use runner to run command and collect dependencies
        self.echo_command(command)
        deps, outputs = self.runner(*arglist)
        if deps is not None or outputs is not None:
            deps_dict = {}
            # hash the dependency inputs and outputs
            for dep in deps:
                hashed = self.hasher(dep)
                if hashed is not None:
                    deps_dict[dep] = "input-" + hashed
            for output in outputs:
                hashed = self.hasher(output)
                if hashed is not None:
                    deps_dict[output] = "output-" + hashed
            self.deps[command] = deps_dict

    def memoize(self, command):
        """ Run the given command, but only if its dependencies have changed --
            like run(), but returns the status code instead of raising an
            exception on error. If "command" is a string (as per memoize.py)
            it's split into args using shlex.split() in a POSIX/bash style,
            otherwise it's a list of args as per run().

            This function is for compatiblity with memoize.py and is
            deprecated. Use run() instead. """
        if isinstance(command, basestring):
            args = shlex.split(command)
        else:
            args = args_to_list(command)
        try:
            self.run(args)
            return 0
        except ExecutionError, exc:
            message, data, status = exc
            return status

    def outofdate(self, func):
        """ Return True if given build function is out of date. """
        self.checking = True
        self.outofdate_flag = False
        func()
        self.checking = False
        return self.outofdate_flag

    def cmdline_outofdate(self, command):
        """ Return True if given command line is out of date. """
        if command in self.deps:
            # command has been run before, see if deps have changed
            for dep, oldhash in self.deps[command].items():
                assert oldhash.startswith('input-') or \
                       oldhash.startswith('output-'), \
                    "%s file corrupt, do a clean!" % self.depsname
                oldhash = oldhash.split('-', 1)[1]
                # make sure this dependency or output hasn't changed
                newhash = self.hasher(dep)
                if newhash is None or newhash != oldhash:
                    break
            else:
                # all dependencies are unchanged
                return False
        # command has never been run, or one of the dependencies didn't
        # exist or had changed
        return True

    def autoclean(self):
        """ Automatically delete all outputs of this build as well as the .deps
            file. """
        # first build a list of all the outputs from the .deps file
        outputs = []
        for command, deps in self.deps.items():
            outputs.extend(dep for dep, hashed in deps.items()
                           if hashed.startswith('output-'))
        outputs.append(os.path.abspath(self.depsname))
        self._deps = None
        for output in outputs:
            try:
                os.remove(output)
            except OSError, e:
                self.echo_delete(output, e)
            else:
                self.echo_delete(output)

    @property
    def deps(self):
        """ Lazy load .deps file so that instantiating a Builder is "safe". """
        if not hasattr(self, '_deps') or self._deps is None:
            self.read_deps()
            atexit.register(self.write_deps)
        return self._deps

    def read_deps(self):
        """ Read dependency JSON file into deps object. """
        try:
            f = open(self.depsname)
            try:
                self._deps = json.load(f)
                # make sure the version is correct
                if self._deps.get('.deps_version', 0) != deps_version:
                    printerr('Bad %s dependency file version! Rebuilding.'
                             % self.depsname)
                    self._deps = {}
                self._deps.pop('.deps_version', None)
            finally:
                f.close()
        except IOError:
            self._deps = {}

    def write_deps(self):
        """ Write out deps object into JSON dependency file. """
        if self._deps is None:
            return                      # we've cleaned so nothing to save
        self.deps['.deps_version'] = deps_version
        f = open(self.depsname, 'w')
        try:
            json.dump(self.deps, f, indent=4, sort_keys=True)
        finally:
            f.close()
            self._deps.pop('.deps_version', None)

    def set_runner(self, runner):
        """Set the runner for this builder.  "runner" is either a callable
           compatible with the Runner class, or a string selecting one of the
           standard runners ("atimes_runner", "strace_runner",
           "always_runner", or "smart_runner")."""
        if runner == 'atimes_runner':
            self.runner = AtimesRunner(self)
        elif runner == 'strace_runner':
            self.runner = StraceRunner(self)
        elif isinstance(runner, basestring):
            self.runner = getattr(self, runner)
        else:
            self.runner = runner

    def smart_runner(self, *args):
        """ Smart command runner that selects which other command
            runner to use based on the environment.  It uses strace if
            it can, otherwise access times if available, otherwise
            always builds. This method overwrites the 'runner'
            attribute, so it will usually be called only the first
            time runner() is used; after that, the selected runner
            will be called directly."""
        if StraceRunner.has_strace():
            self.runner = StraceRunner(self)
        else:
            self.atimes = AtimesRunner.has_atimes(self.dirs)
            if self.atimes==2:
                self.runner = AtimesRunner(self)
            elif self.atimes==1:
                self.runner = AtimesRunner(self)
            else:
                self.runner = self.always_runner
        return self.runner(*args)

    # The default command runner.  Override this in a subclass if you
    # want to write your own auto-dependency runner.
    runner = smart_runner

    def _is_relevant(self, fullname):
        """ Return True if file is in the dependency search directories. """
        for path in self.dirs:
            if fullname.startswith(path):
                rest = fullname[len(path):]
                # files in dirs starting with ignoreprefix are not relevant
                if os.sep+self.ignoreprefix in os.sep+os.path.dirname(rest):
                    continue
                # files deeper than dirdepth are not relevant
                if rest.count(os.sep) > self.dirdepth:
                    continue
                return True
        return False

    def always_runner(self, *args):
        """ Runner that always runs given command, used as a backup in case
            a system doesn't have strace or atimes. """
        shell(*args, **dict(silent=False))
        return None, None

# default Builder instance, used by helper run() and main() helper functions
default_builder = Builder()
default_command = 'build'

def setup(builder=None, default=None, **kwargs):
    """ Setup the default Builder (or an instance of given builder if "builder"
        is not None) with the same keyword arguments as for Builder().
        "default" is the name of the default function to run when the build
        script is run with no command line arguments. """
    global default_builder, default_command
    if builder is not None:
        default_builder = builder()
    if default is not None:
        default_command = default
    default_builder.__init__(**kwargs)

def run(*args):
    """ Run the given command, but only if its dependencies have changed. Uses
        the default Builder. """
    default_builder.run(*args)

def autoclean():
    """ Automatically delete all outputs of the default build. """
    default_builder.autoclean()

def memoize(command):
    return default_builder.memoize(command)

memoize.__doc__ = Builder.memoize.__doc__

def outofdate(command):
    """ Return True if given command is out of date and needs to be run. """
    return default_builder.outofdate(command)

def parse_options(usage):
    """ Parse command line options and return parser and args. """
    parser = optparse.OptionParser(usage='Usage: %prog '+usage,
                                   version='%prog '+__version__)
    parser.disable_interspersed_args()
    parser.add_option('-t', '--time', action='store_true',
                      help='use file modification times instead of MD5 sums')
    parser.add_option('-d', '--dir', action='append',
                      help='add DIR to list of relevant directories')
    parser.add_option('-c', '--clean', action='store_true',
                      help='autoclean build outputs before running')
    parser.add_option('-q', '--quiet', action='store_true',
                      help="don't echo commands, only print errors")
    options, args = parser.parse_args()
    default_builder.quiet = options.quiet
    if options.time:
        default_builder.hasher = mtime_hasher
    if options.dir:
        default_builder.dirs.extend(os.path.abspath(d) for d in options.dir)
    if options.clean:
        default_builder.autoclean()
    return parser, options, args

def main(globals_dict=None):
    """ Run the default function or the function(s) named in the command line
        arguments. Call this at the end of your build script. If one of the
        functions returns nonzero, main will exit with the last nonzero return
        value as its status code. """
    if globals_dict is None:
        try:
            globals_dict = sys._getframe(1).f_globals
        except:
            printerr("Your Python version doesn't support sys._getframe(1),")
            printerr("call main(globals()) explicitly")
            sys.exit(1)

    usage = '[options] build script functions to run'
    parser, options, actions = parse_options(usage)
    if not actions:
        actions = [default_command]

    status = 0
    try:
        for action in actions:
            if '(' not in action:
                action = action.strip() + '()'
            name = action.split('(')[0].split('.')[0]
            if name in globals_dict:
                this_status = eval(action, globals_dict)
                if this_status:
                    status = int(this_status)
            else:
                printerr('%r command not defined!' % action)
                sys.exit(1)
    except ExecutionError, exc:
        message, data, status = exc
        printerr('fabricate: ' + message)
    sys.exit(status)

if __name__ == '__main__':
    # if called as a script, emulate memoize.py -- run() command line
    parser, options, args = parse_options('[options] command line to run')
    status = 0
    if args:
        status = memoize(args)
    elif not options.clean:
        parser.print_help()
        status = 1
    # autoclean may have been used
    sys.exit(status)
