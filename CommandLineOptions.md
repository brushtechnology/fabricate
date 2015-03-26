## Command line options ##

fabricate is intended to be used in a build script, for example, `build.py`. But you can also run `fabricate.py` directly as a script with a command to run given on the command line. See examples of both methods on the [project home page](http://code.google.com/p/fabricate/).

With either method, you can use certain command line options to override the default setup, or the `setup()` given in your build script. These are `-t`, `-d`, `-c` and `-q`, as follows:

```
Usage: fabricate.py [options] command line to run

 Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -t, --time            use file modification times instead of MD5 sums
  -d DIR, --dir=DIR     add DIR to list of relevant directories
  -c, --clean           autoclean build outputs before running
  -q, --quiet           don't echo commands, only print errors
  -D, --debug           show debug info (why commands are rebuilt)
  -k, --keep            keep temporary strace output files
  -j JOBS, --jobs=JOBS  maximum number of parallel jobs
```