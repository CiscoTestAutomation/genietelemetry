#! /bin/env python

'''Setup file for GenieTelemetry

See: 
    https://packaging.python.org/en/latest/distributing.html
'''
import os
from ciscodistutils import setup, find_packages, is_devnet_build
from ciscodistutils.tools import (read,
                                  version_info,
                                  generate_cython_modules)

from ciscodistutils.common import (AUTHOR,
                                   URL,
                                   CLASSIFIERS,
                                   PYATS_PKG,
                                   SUPPORT,
                                   LICENSE,
                                   STD_EXTRA_REQ)

# get version information
version, version_range = version_info('src',
                                      'genie',
                                      'telemetry',
                                      '__init__.py')

install_requires=['setuptools', 'wheel',
                  'genie.abstract',
                  'genie.libs.telemetry']

# launch setup
setup(
    name = 'genie.telemetry',
    version = version,

    # descriptions
    description = 'testbed health status monitoring tool',
    long_description = read('DESCRIPTION.rst'),

    # the project's main homepage.
    url = URL,

    # author details
    author = AUTHOR,
    author_email = SUPPORT,

    # project licensing
    license = LICENSE,

    # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = CLASSIFIERS,

    # project keywords
    keywords = 'genie telemetry pyats cisco',

    # uses namespace package
    namespace_packages = ['genie'],

    # project packages
    packages = find_packages(where = 'src'),

    # project directory
    package_dir = {
        '': 'src',
    },

    # additional package data files that goes into the package itself
    package_data = {
        '': ['README.rst']
    },

    # custom argument specifying the list of cythonized modules
    cisco_cythonized_modules = generate_cython_modules('src/'),

    # console entry point
    entry_points = { 
        'console_scripts': ['genietelemetry = genie.telemetry:main'],
    },

    # package dependencies
    install_requires = install_requires,

    # any additional groups of dependencies.
    # install using: $ pip install -e .[dev]
    extras_require = {
        'dev': ['coverage',
                'restview',
                'Sphinx',
                'sphinx-rtd-theme',
                'sphinxcontrib-mockautodoc'],
    },

    # external modules
    ext_modules = [],

    # any data files placed outside this package. 
    # See: http://docs.python.org/3.4/distutils/setupscript.html
    # format:
    #   [('target', ['list', 'of', 'files'])]
    # where target is sys.prefix/<target>
    data_files = [],
    
    # non zip-safe (never tested it)
    zip_safe = False,
)
