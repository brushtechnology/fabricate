from setuptools import setup

from fabricate import __version__

readme = open('README.md').read()

setup(
    name='fabricate',
    version=__version__,
    description='The better build tool. Finds dependencies automatically for any language.',
    long_description=readme,
    author='Brush Technology',
    url='https://github.com/SimonAlfie/fabricate/',
    py_modules=['fabricate'],

    extras_require=dict(
        build=['twine', 'wheel', 'setuptools-git'],
    ),

    keywords='fabricate make python build',
    classifiers=[
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
)


