# -*- coding: utf-8 -*-

# flake8: noqa

""" Python 2/3 compatibility wrapper. """

from __future__ import absolute_import, print_function

import sys

py3k = sys.version_info[:2] >= (3, 0)


if py3k:
    string_types = str,

    def cmp(a, b):
        """
        Compare two objects and return an integer according to the outcome.

        https://docs.python.org/2/library/functions.html#cmp

        In Python 3: "The cmp() function should be treated as gone"

        https://docs.python.org/3.0/whatsnew/3.0.html#ordering-comparisons
        """
        return (a > b) - (a < b)

    def b(s):
        """
        Turn a string into bytes.

        Python 3 strings aren't a list of bytes, but Python 2 strings are; this
        provides a conversion wrapper.
        """
        return s.encode("utf-8")

    from urllib.parse import quote, quote_plus, urlencode
    from urllib.parse import urlparse, parse_qs, parse_qsl

    from urllib.request import Request, urlopen
    from urllib.error import URLError

else:
    string_types = basestring,

    cmp = cmp

    def b(s):
        """
        Dummy function for compatibility reasons.

        This converts a string into a list of bytes, which in Python 2 means
        doing nothing, but for Python 3 requires explicit conversion.
        """
        return s

    from urllib import quote, quote_plus, urlencode

    from urlparse import urlparse, parse_qs, parse_qsl

    from urllib2 import Request, urlopen, URLError

