import os

from fabricate import main, shell, autoclean

def build():
    print("No package building supported yet. Maybe someday.")
    print("You probably want to run the 'test' target.")

def test():
    # kind of lame, but will do until we get better unit tests
    here = os.getcwd()
    for f in os.listdir("test"):
        dir = os.path.join("test", f)
        if os.path.isdir(dir):
            print("Testing " + f + "...")
            os.chdir(dir)
            # can't use run() on the tests because they're going to use 
            # fabricate to trace and you can't double-trace a process
            shell('python', 'build.py')
            os.chdir(here)

def clean():
    autoclean()

main()

