from setuptools import setup

from fabricate import __version__


readme = open('README.md').read()

setup(
    name='fabricate',
    version=__version__,
    description = 'Build tool that finds dependencies automatically for any language.',
    long_description = readme,
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Build Tools'
    ],
    author='Brush Technology',
    keywords='fabricate make python',
    py_modules=['fabricate']
)


