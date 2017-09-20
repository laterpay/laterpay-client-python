# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

import codecs
import os

_version = "5.4.0"
_packages = find_packages('.', exclude=["*.tests", "*.tests.*", "tests.*", "tests"])

if os.path.exists('README.rst'):
    _long_description = codecs.open('README.rst', 'r', 'utf-8').read()
else:
    _long_description = ""

setup(
    name='laterpay-client',
    version=_version,

    description="LaterPay API client",
    long_description=_long_description,
    author="LaterPay GmbH",
    author_email="support@laterpay.net",
    url="https://github.com/laterpay/laterpay-client-python",
    license='MIT',
    keywords="LaterPay API client",

    test_suite="tests",

    packages=_packages,

    install_requires=[
        'PyJWT>=1.4.2',
        'requests',
        'six',
    ],

    classifiers=(
        # "Development Status :: 3 - Alpha",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ),
)
