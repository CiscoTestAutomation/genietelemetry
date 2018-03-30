#! /bin/env python

'''Setup file for GenieTelemetry

See: 
    https://packaging.python.org/en/latest/distributing.html
'''
import os, re
from setuptools import setup, find_packages

def read(*paths):
    '''read and return txt content of file'''
    with open(os.path.join(*paths)) as fp:
        return fp.read()

def find_version(*paths):
    '''reads a file and returns the defined __version__ value'''
    version_match = re.search(r"^__version__ ?= ?['\"]([^'\"]*)['\"]",
                              read(*paths), re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

def find_templates(*paths):
    '''finds all template files'''
    files = []
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(*paths)):
        files.append((dirpath, [os.path.join(dirpath, f) for f in filenames]))

    return files

version = find_version('src', 'genie', 'telemetry', '__init__.py')

# launch setup
setup(
    name = 'genie.telemetry',
    version = version,

    # descriptions
    description = 'Genie.Telemetry: Testbed Telemetry Service',
    long_description = read('DESCRIPTION.rst'),

    # the project's main homepage.
    url = 'http://wwwin-pyats.cisco.com/',

    # author details
    author = 'ASG/ATS Teams',
    author_email = 'python-core@cisco.com',

    # project licensing
    license = 'Cisco Systems, Inc. Cisco Confidential',

    # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Telecommunications Industry'
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Testing',
    ],

    # project keywords
    keywords = 'testbed health status monitoring',

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
        '': ['tests/*.py',
             'tests/scripts/*.py',
             'tests/scripts/*.yaml',
             'tests/scripts/*.html',
            ]
    },

    # custom argument specifying the list of cythonized modules
    #pyats_cythonized_modules = generate_cython_modules('src/'),

    # console entry point
    entry_points = { 
        'console_scripts': ['genietelemetry = genie.telemetry:main'],
    },

    # package dependencies
    install_requires =  ['ats.async >= 3.3.0',
                         'ats.datastructures >= 3.3.0',
                         'ats.log >= 3.3.0',
                         'ats.utils >= 3.3.0',
                         'ats.topology >= 3.3.0',
                         'abstract',
                        ],

    # any additional groups of dependencies.
    # install using: $ pip install -e .[dev]
    extras_require = {
    },

    # external modules
    ext_modules =[],

    # any data files placed outside this package. 
    # See: http://docs.python.org/3.4/distutils/setupscript.html
    # format:
    #   [('target', ['list', 'of', 'files'])]
    # where target is sys.prefix/<target>
    data_files = find_templates('templates'),
    
    # non zip-safe (never tested it)
    zip_safe = False,
)
