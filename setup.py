#!/usr/bin/env python3

from pathlib import Path

import setuptools

setuptools.setup(
    name='parsita',
    version='1.4.0',

    description='Parser combinator library for Python.',
    long_description=Path('README.rst').read_text(encoding='utf-8'),
    keywords='parser combinator',

    author='David Hagen',
    author_email='david@drhagen.com',
    url='https://github.com/drhagen/parsita',
    license='MIT',

    package_dir={'': 'src'},
    packages=setuptools.find_packages('src'),

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
