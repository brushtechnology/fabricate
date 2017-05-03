from setuptools import setup

from fabricate import __version__

# see https://github.com/pypa/pypi-legacy/issues/148
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = open('README.md').read()

setup(
    name='fabricate',
    version=__version__,
    description='The better build tool. Finds dependencies automatically for any language.',
    long_description=long_description,
    license='New BSD License',
    maintainer='Chris Coetzee',
    maintainer_email='chriscz93@gmail.com',
    url='https://github.com/SimonAlfie/fabricate/',
    py_modules=['fabricate'],

    extras_require=dict(
        build=['twine', 'wheel', 'setuptools-git', 'pypandoc'],
    ),

    keywords='fabricate make python build',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    platforms=[
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux'
    ]
)


