# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six


if six.PY3:
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
else:
    cmp = cmp

    def b(s):
        """
        Dummy function for compatibility reasons.

        This converts a string into a list of bytes, which in Python 2 means
        doing nothing, but for Python 3 requires explicit conversion.
        """
        return s


def encode_if_unicode(value, encoding='utf-8'):
    """
    Encode and return a ``value`` using specified ``encoding``.

    Encoding is done only if ``value`` is a ``unicode`` instance
    (utf-8 encoding is used as default).
    """
    if six.PY2 and isinstance(value, unicode):
        value = value.encode(encoding)
    return value
