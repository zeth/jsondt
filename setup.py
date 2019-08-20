"""Setup for jsondt module."""

try:
    from setuptools import setup
except ImportError:
    SETUPTOOLS = False
    from distutils.core import setup
else:
    SETUPTOOLS = True

import jsondt

CLASSIFIERS = [
    "Programming Language :: Python :: 3.7",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
    "Topic :: Internet :: WWW/HTTP",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: MacOS :: MacOS X",
]

SHORT_DESC = 'JSON module with added datetime support.'

with open("README.rst", "r") as fp:
    LONG_DESCRIPTION = fp.read()

KWARGS = {
    'name': 'jsondt',
    'description': SHORT_DESC,
    'version': jsondt.__version__,
    'author': 'Zeth Green',
    'author_email': 'theology@gmail.com',
    'py_modules': ['jsondt'],
    'long_description': LONG_DESCRIPTION,
    'license': "BSD",
    'classifiers': CLASSIFIERS,
    'url': 'https://github.com/zeth/jsondt',
}

if SETUPTOOLS:
    KWARGS['test_suite'] = 'test_jsondt.py'


setup(**KWARGS)
