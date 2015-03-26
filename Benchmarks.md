These benchmarks were run using the benchmark.py script in the source tree. This script creates a bunch of C source and header files, and then when you tell it to build, it creates a fabricate build.py script which it runs using the given runner.

There's also a comparison against `make` for each platform.

## Windows ##

Tested using fabricate v1.20 ([76e490eccaaf](https://code.google.com/p/fabricate/source/browse/?r=76e490eccaaf9ef848187dce7f23725290f74655)) on a Windows XP 32-bit system, compiles done with tcc (Tiny C Compiler). Number of sources/lines/headers/lines 100/1000/10/10000. Times below are normalized so AlwaysRunner is 1.0:

| **Runner** | **Time (normalized)** |
|:-----------|:----------------------|
| AlwaysRunner | 1.00 |
| AtimesRunner first build | 1.02 |
| AtimesRunner subsequent builds | 0.0073 |
| make first build | 1.05 |
| make subsequent builds | 0.011 |

## Linux ##

Tested using fabricate v1.20 ([76e490eccaaf](https://code.google.com/p/fabricate/source/browse/?r=76e490eccaaf9ef848187dce7f23725290f74655)) on a Linux system (Huck), compiles done with gcc. Number of sources/lines/headers/lines 25/250/5/500 (because gcc is so much slower than tcc!). Times below are normalized so AlwaysRunner is 1.0:

| **Runner** | **Time (normalized)** |
|:-----------|:----------------------|
| AlwaysRunner | 1.00 |
| StraceRunner first build | 1.19 |
| StraceRunner subsequent builds | 0.011 |
| make first build | 0.99 |
| make subsequent builds | 0.00049 |

## Linux with parallel jobs ##

Tested using fabricate v1.20 ([6754093560ae](https://code.google.com/p/fabricate/source/browse/?r=6754093560ae88438b2aaf5d5fedc248e756cf2f)) on a quad-core Linux system. Number of sources/lines/headers/lines 100/1000/10/10000, and with parallel\_ok=True and different numbers of jobs (results accurate to +/- 2%):

With `--jobs=1`:

| **Runner** | **Time (normalized)** |
|:-----------|:----------------------|
| AlwaysRunner | 1.00 |
| StraceRunner first build | 1.00 |
| StraceRunner subsequent builds | 0.0013 |
| make first build | 0.97 |
| make subsequent builds | 0.000054 |

With `--jobs=2`:

| **Runner** | **Time (normalized)** |
|:-----------|:----------------------|
| AlwaysRunner | 1.00 |
| StraceRunner first build | 0.54 |
| StraceRunner subsequent builds | 0.0015 |
| make first build | 0.56 |
| make subsequent builds | 0.000054 |

With `--jobs=3`:

| **Runner** | **Time (normalized)** |
|:-----------|:----------------------|
| AlwaysRunner | 1.00 |
| StraceRunner first build | 0.40 |
| StraceRunner subsequent builds | 0.0016 |
| make first build | 0.41 |
| make subsequent builds | 0.000043 |

With `--jobs=4`:

| **Runner** | **Time (normalized)** |
|:-----------|:----------------------|
| AlwaysRunner | 1.00 |
| StraceRunner first build | 0.41 |
| StraceRunner subsequent builds | 0.0016 |
| make first build | 0.39 |
| make subsequent builds | 0.000043 |