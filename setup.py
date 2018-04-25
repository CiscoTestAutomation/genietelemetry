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


_INTERNAL_SUPPORT = 'pyats-support@cisco.com'
_EXTERNAL_SUPPORT = 'pyats-support-ext@cisco.com'

_INTERNAL_LICENSE = 'Cisco Systems, Inc. Cisco Confidential',
_EXTERNAL_LICENSE = 'Apache 2.0'

_INTERNAL_URL = 'http://wwwin-pyats.cisco.com/cisco-shared/genietelemetry/html/'
_EXTERNAL_URL = 'https://developer.cisco.com/site/pyats/'


# pyats support mailer
SUPPORT = _EXTERNAL_SUPPORT if is_devnet_build() else _INTERNAL_SUPPORT

# license statement
LICENSE = _EXTERNAL_LICENSE if is_devnet_build() else _INTERNAL_LICENSE

# project url
URL = _EXTERNAL_URL if is_devnet_build() else _INTERNAL_URL

# pyats package
PYATS_PKG = 'pyats' if is_devnet_build() else 'ats'

# get version information
version, version_range = version_info('src',
                                      'genie',
                                      'telemetry',
                                      '__init__.py')

install_requires=['setuptools', 'wheel',
                  'genie.abstract >= 1.1.1',
                  'genie.libs.telemetry',
                  '{package} >= {range}'.format(package = PYATS_PKG,
                                                range = '4.1.0')]

# launch setup
setup(
    name = 'genie.telemetry',
    version = version,

    # descriptions
    description = 'Genie Library for testbed telemetry support',
    long_description = read('DESCRIPTION.rst'),

    # the project's main homepage.
    url = URL,

    # author details
    author = 'Cisco Systems Inc.',
    author_email = SUPPORT,

    # project licensing
    license = LICENSE,

    # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Telecommunications Industry',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],


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
                'sphinxcontrib-napoleon',
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
