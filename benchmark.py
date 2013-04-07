"""Simple benchmark for fabricate."""
from __future__ import print_function

import os
import shutil
import sys
import time

import fabricate

COMPILER = None
BUILD_DIR = 'benchproject'
NUM_SOURCE_FILES = 100
NUM_SOURCE_LINES = 1000

NUM_HEADER_FILES = 10
NUM_HEADER_LINES = 10000

if sys.platform == 'win32':
    # time.clock() is much more accurate under Windows
    get_time = time.clock
else:
    get_time = time.time

def delete_deps():
    if os.path.exists(os.path.join(BUILD_DIR, '.deps')):
        os.remove(os.path.join(BUILD_DIR, '.deps'))

def generate():
    if not os.path.exists(BUILD_DIR):
        os.mkdir(BUILD_DIR)
    delete_deps()

    for source_index in range(NUM_SOURCE_FILES):
        lines = []

        for header_index in range(NUM_HEADER_FILES):
            lines.append('#include "header%d.h"' % header_index)

        if source_index == 0:
            lines.append('#include <stdio.h>')
            lines.append('int main(void) {')
            for source_index2 in range(NUM_SOURCE_FILES):
                for line_index in range(NUM_SOURCE_LINES):
                    lines.append('    printf("%%d ", func%d_%d(42, 24));' %
                                 (source_index2, line_index))
            lines.append('}')

        for line_index in range(NUM_SOURCE_LINES):
            lines.append('int func%d_%d(int x, int y) { return x * %d + y * %d; }' %
                         (source_index, line_index, source_index, line_index))

        filename = os.path.join(BUILD_DIR, 'source%d.c' % source_index)
        f = open(filename, 'w')
        f.write('\n'.join(lines))
        f.close()
    
    for header_index in range(NUM_HEADER_FILES):
        lines = []
        lines.append('#ifndef HEADER%d_H' % header_index)
        lines.append('#define HEADER%d_H' % header_index)

        if header_index == 0:
            for source_index2 in range(NUM_SOURCE_FILES):
                for line_index in range(NUM_SOURCE_LINES):
                    lines.append('int func%d_%d(int x, int y);' %
                                 (source_index2, line_index))
        
        for line_index in range(NUM_HEADER_LINES):
            lines.append('typedef int type_%d_%d;' % (header_index, line_index))
        
        lines.append('#endif')

        filename = os.path.join(BUILD_DIR, 'header%d.h' % header_index)
        f = open(filename, 'w')
        f.write('\n'.join(lines))
        f.close()

def benchmark(runner, jobs):
    if runner == 'always_runner':
        delete_deps()

    para = (', parallel_ok=True, jobs=%d' % jobs) if jobs > 1 else ''
    build_file = r"""
from fabricate import *

sources = [
    %s
]

def build():
    compile()
    after()
    link()

def compile():
    for source in sources:
        run(%s, '-c', source + '.c')

def link():
    objects = [s + '.o' for s in sources]
    run(%s, '-o', 'benchmark', objects)

def clean():
    autoclean()

main(runner='%s'%s)
""" % (',\n    '.join("'source%d'" % i for i in range(NUM_SOURCE_FILES)),
       repr(COMPILER),
       repr(COMPILER),
       runner,
       para)

    filename = os.path.join(BUILD_DIR, 'build.py')
    f = open(filename, 'w')
    f.write(build_file)
    f.close()

    time0 = get_time()
    filename = os.path.join(BUILD_DIR, 'build.py')
    fabricate.shell('python', filename, '-q')
    elapsed_time = get_time() - time0
    return elapsed_time

def benchmake(jobs):
    makefile = """
OBJECTS = \\
\t%s

benchmark: $(OBJECTS)
\t"%s" -o benchmark $(OBJECTS)

%%.o: %%.c
\t"%s" -c $< -o $@

%%.c: \\
\t%s
""" % (' \\\n\t'.join('source%d.o' % i for i in range(NUM_SOURCE_FILES)),
       COMPILER,
       COMPILER,
       ' \\\n\t'.join('header%d.h' % i for i in range(NUM_HEADER_FILES)))

    filename = os.path.join(BUILD_DIR, 'Makefile')
    f = open(filename, 'w')
    f.write(makefile)
    f.close()

    time0 = get_time()
    filename = os.path.join(BUILD_DIR, 'build.py')
    job_arg = '-j%d' % jobs
    fabricate.shell('make', job_arg, '-s', '-C', BUILD_DIR)
    elapsed_time = get_time() - time0
    return elapsed_time

def clean():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)

def usage():
    print('Usage: benchmark.py compiler generate|benchmark [runner=smart_runner [jobs=1]]|benchmake [jobs=1]|clean')
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage()
    orig_cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    jobs = 1
    try:
        COMPILER = sys.argv[1]
        if sys.argv[2] == 'generate':
            generate()
        elif sys.argv[2] == 'benchmark':
            if len(sys.argv) > 3:
                runner = sys.argv[3]
            else:
                runner = 'smart_runner'
            if len(sys.argv) > 4:
                jobs = int(sys.argv[4])
            print(benchmark(runner, jobs))
        elif sys.argv[2] == 'benchmake':
            if len(sys.argv) > 3:
                jobs = int(sys.argv[3])
            print(benchmake(jobs))
        elif sys.argv[2] == 'clean':
            clean()
        else:
            usage()
    finally:
        os.chdir(orig_cwd)
