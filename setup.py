#!/usr/bin/env python

import os

from setuptools import setup

curdir = os.path.dirname(os.path.abspath(__file__))


with open(os.path.join(curdir, 'ldif3.py')) as fh:
    for line in fh:
        if line.startswith('"""'):
            name, description = line.rstrip().strip('"').split(' - ')
        elif line.startswith('__version__'):
            version = line.split('\'')[1]
            break

setup(
    name=name,
    version=version,
    description=description,
    long_description=open(os.path.join(curdir, 'README.rst')).read(),
    url='https://github.com/xi/ldif3',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    py_modules=['ldif3'],
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Topic :: System :: Systems Administration :: '
            'Authentication/Directory :: LDAP',
    ])
