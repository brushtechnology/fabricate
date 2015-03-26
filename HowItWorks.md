If you're looking for detailed [usage help](Help.md), look on that link.

## Finding dependencies automatically ##

fabricate lets you simply type `run('command', 'arg1', 'arg2')`, and it will run the command and figure out its dependencies (and outputs) automatically. Next time it'll only actually execute the command if those dependencies have changed (or the outputs have been modified or don't exist).

It finds dependencies by one of two methods:

  * **strace:** fabricate first tries to use the Linux `strace` command to log system calls to `open()` and determines what files were read and modified that way.
  * **File access times (atimes):** Some systems (Windows) don't have `strace`, and in that case fabricate looks at the atimes of files before and after the command was run, and from those can figure out which files each command accesses. It also uses file modification times (mtimes) to determine the command's output files. It's fast and simple, and it works on NTFS, FAT32 (thanks to some tricks), as well as Linux file systems that have atimes enabled.

### Windows Issues ###

**WARNING: Windows** use of Fabricate has **gotchas** until somebody implements something better than the atimes dependency calculator.  The gotchas and an strace-like solution are discussed [in this forum thread](http://code.google.com/p/fabricate/issues/detail?id=14).  If you are running **Windows Vista or higher**, you will probably need to issue the command "fsutil behavior set disablelastaccess 0" before fabricate and atimes will work. The [designers](http://brush.co.nz/contact) of fabricate are **willing to make a more robust Windows solution** if somebody wants to pay for development time. For now we are satisfied to use it with gotchas.

fabricate automatically picks between these two methods. In the unusual case that neither method is supported by your system, fabricate will fall back to always running the command. (Contact us if you're having problems with your setup.)

You can of course choose your own adventure and customize how fabricate works. Just subclass the `fabricate.Runner` class and pass it in the `setup()` function. See the [GccRunner class](HowtoMakeYourOwnRunner.md) for an example of using gcc to determine dependencies.

## Storing the dependency list ##

fabricate stores the list of input and output files and their MD5 sums for each command in a file called `.deps` (by default).

If you're running Python 2.6 or you have [simplejson](http://pypi.python.org/pypi/simplejson/) installed, this will be a nice, human-readable JSON file. Otherwise fabricate will use pickle -- less readable, but just as good for building.

Here's what the .deps file looks like for the build example on the project home page:

```
{
    ".deps_version": 1, 
    "gcc -c program.c": {
        "C:\\work\\example\\program.c": "input-cf7173408d93621bfd3d7a455291e277", 
        "C:\\work\\example\\program.o": "output-4a654dfd885a57f2dc7ccf657014167b", 
        "C:\\work\\example\\util.h": "input-b411187d14ef4c2d7df045134a5d555d"
    }, 
    "gcc -c util.c": {
        "C:\\work\\example\\util.c": "input-c5cbf91d7076fdcd2a85335ac075fe24", 
        "C:\\work\\example\\util.h": "input-b411187d14ef4c2d7df045134a5d555d", 
        "C:\\work\\example\\util.o": "output-44801837997d4d0e4588335fa01f6ce8"
    }, 
    "gcc -o program program.o util.o": {
        "C:\\work\\example\\program.exe": "output-2da016e470175217d298d4645e8ce4ad", 
        "C:\\work\\example\\program.o": "input-4a654dfd885a57f2dc7ccf657014167b", 
        "C:\\work\\example\\util.o": "input-44801837997d4d0e4588335fa01f6ce8"
    }
}
```

## Checking for differences ##

fabricate checks whether files are different by doing an MD5 hash on their contents, using `md5_hasher()`. You can change this to use modification times like make by calling `setup(hasher=mtime_hasher)` in your build script.

You can also write your own hasher function, of course, though we've never had need to.