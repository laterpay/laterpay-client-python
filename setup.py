# -*- coding: UTF-8 -*-
from distutils.core import setup
from setuptools import find_packages

import codecs

#import time
#_version = "3.0.dev%s" % int(time.time())
_version = "3.0.0"
_packages = find_packages('.', exclude=["*.tests", "*.tests.*", "tests.*", "tests"])

setup(
    name='laterpay-client',
    version=_version,

    description="LaterPay API client",
    long_description=codecs.open("README.rst", encoding='utf-8').read(),
    author="LaterPay GmbH",
    author_email="support@laterpay.net",
    url="https://github.com/laterpay/laterpay-client-python",
    license='MIT',
    keywords="LaterPay API client",

    test_suite="test_client",

    packages=_packages,
    package_data={'laterpay.django': ['templates/laterpay/inclusion/*']},

    classifiers=(
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ),
)
