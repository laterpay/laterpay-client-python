# -*- coding: utf-8 -*-
import warnings

import six


def encode_if_unicode(value, encoding='utf-8'):  # pragma: no cover
    """
    Encode and return a ``value`` using specified ``encoding``.

    Encoding is done only if ``value`` is a ``unicode`` instance
    (utf-8 encoding is used as default).

    .. deprecated:: 5.0.0

        Use :func:`laterpay.compat.stringify` instead.
    """
    warnings.warn(
        'laterpay.compat.encode_if_unicode is deprecated and will be removed '
        'in future versions. Use laterpay.compat.stringify instead',
        DeprecationWarning
    )

    if six.PY2 and isinstance(value, six.text_type):
        value = value.encode(encoding)
    return value


def stringify(value):
    """
    Convert ``value`` into a native Python string.

    If value is not a byte- or unicode-string the function calls ``str()`` on
    it.

    If the value then is a unicode string (on Python 2) or byte string (on
    Python 3) the function converts it into the respective native string type
    (byte string on Python 2; unicode string on Python 3).

    In all other cases the value is returned as-is.
    """
    if not isinstance(value, (six.string_types, six.binary_type)):
        # If any non-string or non-bytes like objects, ``str()`` them.
        value = str(value)
    if six.PY3 and isinstance(value, six.binary_type):
        # Issue #84, decode byte strings before using them on Python 3
        value = value.decode()
    elif six.PY2 and isinstance(value, six.text_type):
        value = value.encode('utf-8')
    return value


def byteify(value):
    """
    Convert ``value`` into a byte-string.
    """
    if isinstance(value, six.text_type):
        return value.encode('utf-8')
    return value
