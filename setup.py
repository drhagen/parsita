#!/usr/bin/env python3

import setuptools


setuptools.setup(
    name='parsita',
    version='0.1.0',

    description='Parser combinator library for Python.',
    long_description=open('README.md').read(),
    keywords='parser combinator',

    author='David Hagen',
    author_email='david@drhagen.com',
    url='https://github.com/drhagen/parsita',
    license='GPLv3',

    packages=setuptools.find_packages(),

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
)
