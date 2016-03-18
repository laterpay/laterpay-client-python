# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six


def encode_if_unicode(value, encoding='utf-8'):
    """
    Encode and return a ``value`` using specified ``encoding``.

    Encoding is done only if ``value`` is a ``unicode`` instance
    (utf-8 encoding is used as default).
    """
    if six.PY2 and isinstance(value, unicode):
        value = value.encode(encoding)
    return value
