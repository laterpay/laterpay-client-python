#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys

py3k = sys.version_info[:2] >= (3, 0)


if py3k:
    string_types = str,

    def cmp(a, b):
        return (a > b) - (a < b)

    def b(s):
        return s.encode("utf-8")

    from urllib.parse import quote, quote_plus, urlencode
    from urllib.parse import urlparse, parse_qs, parse_qsl

    from urllib.request import Request, urlopen
    from urllib.error import URLError

else:
    string_types = basestring,

    cmp = cmp

    def b(s):
        return s

    from urllib import quote, quote_plus, urlencode

    from urlparse import urlparse, parse_qs, parse_qsl

    from urllib2 import Request, urlopen, URLError

