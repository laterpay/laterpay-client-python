# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import hashlib
import hmac

import six
from six.moves.urllib.parse import quote, urlparse
try:
    from furl.omdict1D import omdict
    HAS_FURL = True
except ImportError:  # pragma: no cover
    HAS_FURL = False

from . import compat

ALLOWED_METHODS = ('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD')


def time_independent_HMAC_compare(a, b):
    """
    No-one likes timing attacks.

    This function should probably not be part of the public API, and thus will
    be deprecated in a future release to be replaced with a internal function.
    """
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def create_HMAC(HMAC_secret, *parts):
    """
    Return the standard LaterPay HMAC of `*parts`.

    This function should probably not be part of the public API, and thus will
    be deprecated in a future release to be replaced with a internal function.
    """
    authcode = hmac.new(six.b(HMAC_secret), digestmod=hashlib.sha224)
    for part in parts:
        authcode.update(six.b(part))
    return authcode.hexdigest()


def sort_params(param_dict):
    """
    Sort a key-value mapping with non-unique keys.

    This function should probably not be part of the public API, and thus will
    be deprecated in a future release to be replaced with a internal function.
    """
    param_list = []
    for name, value_list in six.iteritems(param_dict):
        if isinstance(value_list, (list, tuple)):
            param_list.extend((name, value) for value in value_list)
        else:
            param_list.append((name, value_list))

    return sorted(param_list)


def normalise_param_structure(params):
    """
    Canonicalise representation of key-value data with non-unique keys.

    Request parameter dictionaries are handled in different ways in different
    libraries. This function is required to ensure we always have something of
    the format::

        {
            'key1': ['value1', 'value2'],
            'key2': ['value3'],
        }

    :param dict, list, tuple, furl.omdict1D.omdict params: The parameter
        structure to normalize. Can be either a ``dict``, ``list``, ``tuple``
        or ``furl.omdict1D.omdict``. The following formats are allowed::

            # A dictionary with key-value or key-values mappings
            {
                'key1': 'value',
                'key2': ['value1', 'value2'],
                'key3': ('value1', 'value2'),
            }

            # A list (or tuple, can be used interchangeably)
            [
                ['key1', 'value1'],
                ['key1', 'value2'],
                ['key2', ['value1', 'value2']],
            ]

    """
    if isinstance(params, dict):
        iterator = six.iteritems(params)
    elif isinstance(params, (list, tuple)):
        iterator = params
    elif HAS_FURL and isinstance(params, omdict):
        iterator = params.iterallitems()
    else:
        raise TypeError('params needs to be dict, list or tuple. It is a %r' % type(params))

    out = {}
    for param_name, param_value in iterator:
        param_name = compat.stringify(param_name)
        out.setdefault(param_name, [])
        if isinstance(param_value, (list, tuple)):
            # this is (a, (b, c)) or { a => (b, c) }
            out[param_name].extend(compat.stringify(v) for v in param_value)
        else:
            # this is ((a, b), (a, c)) or { a => b }
            out[param_name].append(compat.stringify(param_value))

    return out


def create_base_message(params, url, method='POST'):
    """
    Construct a message to be signed.

    You are unlikely to need to call this directly and should not consider it a
    stable part of the API. This will be deprecated and replaced with a internal
    method accordingly, in a future release.

    http://docs.laterpay.net/platform/intro/signing_urls/
    """
    msg = '{method}&{url}&{params}'

    method = compat.encode_if_unicode(method).upper()

    data = {}

    url = quote(compat.encode_if_unicode(url), safe='')

    if method not in ALLOWED_METHODS:
        raise ValueError('method should be one of: {}'.format(ALLOWED_METHODS))

    params = normalise_param_structure(params)

    for key, values in six.iteritems(params):
        key = quote(compat.encode_if_unicode(key), safe='')

        values_str = []

        for value in values:
            if not isinstance(value, (six.string_types, six.binary_type)):
                # If any non-string or non-bytes like objects, ``str()`` them.
                value = str(value)
            if six.PY3 and isinstance(value, six.binary_type):
                # Issue #84, decode byte strings before using them on Python 3
                value = value.decode()
            values_str.append(value)

        data[key] = [quote(compat.encode_if_unicode(value_str), safe='') for value_str in values_str]

    sorted_params = sort_params(data)

    param_str = '&'.join('{}={}'.format(k, v) for k, v in sorted_params)
    param_str = quote(param_str, safe='')

    return msg.format(method=method, url=url, params=param_str)


def sign(secret, params, url, method='POST'):
    """
    Create signature for given `params`, `url` and HTTP `method`.

    :param secret: secret string used to create the signature
    :param params: params dict (values can be strings or lists of strings)
    :param url: base url for which the params were signed.
                Example: https://example.net/here
                (no query params or fragments)
    :param method: HTTP method used to transport the signed data
                   ('POST' is default)
    """
    if 'hmac' in params:
        params.pop('hmac')

    if 'gettoken' in params:
        params.pop('gettoken')

    secret = compat.encode_if_unicode(secret)

    url_parsed = urlparse(url)
    base_url = url_parsed.scheme + "://" + url_parsed.netloc + url_parsed.path

    msg = create_base_message(params, base_url, method=method)

    mac = create_HMAC(secret, msg)

    return mac


def verify(signature, secret, params, url, method):
    """
    Verify the signature of a given `params` dict.

    :param signature: signature string to be verified
    :param secret: secret string used to create the signature
    :param params: params dict (values can be strings or lists of strings)
    :param url: base url for which the params were signed.
                Example: https://example.net/here
                (no query params or fragments)
    :param method: HTTP method used to transport the signed data
    """
    if isinstance(signature, (list, tuple)):
        signature = signature[0]

    mac = sign(secret, params, url, method)

    return time_independent_HMAC_compare(signature, mac)
