# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import hashlib
import hmac
import time
import warnings

import six
from six.moves.urllib.parse import parse_qsl, quote, urlencode, urlparse

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
            for value in value_list:
                if not isinstance(value, six.string_types):
                    value = str(value)
                param_list.append((name, value))
        else:
            if not isinstance(value_list, six.string_types):
                value_list = str(value_list)
            param_list.append((name, value_list))

    return sorted(param_list)


def normalise_param_structure(params):
    """
    Canonicalise representation of key-value data with non-unique keys.

    Request parameter dictionaries are handled in different ways in different libraries,
    this function is required to ensure we always have something of the format:

       {  key:  [ value1, value2... ] }

    """
    out = {}

    if isinstance(params, (list, tuple)):
        # this is tricky - either we have (a, b), (a, c) or we have (a, (b, c))
        for param_name, param_value in params:
            if isinstance(param_value, (list, tuple)):
                # this is (a, (b, c))
                out[param_name] = param_value
            else:
                # this is (a, b), (a, c)
                if param_name not in out:
                    out[param_name] = []
                out[param_name].append(param_value)
        return out

    # otherwise this is a dictionary, so either it is { a => b } or { a => (b,c) }
    for key, value in six.iteritems(params):
        if not isinstance(value, (list, tuple)):
            out[key] = [value]
        else:
            out[key] = value

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

        # If any non six.string_types objects, ``str()`` them.
        for value in values:
            if not isinstance(value, six.string_types):
                value = str(value)
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


def sign_and_encode(secret, params, url, method="GET"):  # pragma: no cover
    """
    Deprecated. Consider using ``laterpay.utils.signed_query()`` instead.

    Sign and encode a URL ``url`` with a ``secret`` key called via an HTTP ``method``.

    It adds the signature to the URL
    as the URL parameter "hmac" and also adds the required timestamp parameter "ts" if it's not already
    in the ``params`` dictionary. ``unicode()`` instances in params are handled correctly.

    :param secret: The shared secret as a hex-encoded string
    :param params: A dictionary of URL parameters. Each key can resolve to a
                   single value string or a multi-string list.
    :param url: The URL being called
    :param method: An uppercase string representation of the HTTP method being
                   used for the call (e.g. "GET", "POST")
    :return: A signed and correctly encoded URL
    """
    warnings.warn(
        "sign_and_encode is deprecated. It will be removed in a future release. "
        "Consider using ``laterpay.utils.signed_query()`` instead.",
        DeprecationWarning,
    )

    if 'ts' not in params:
        params['ts'] = str(int(time.time()))

    if 'hmac' in params:
        params.pop('hmac')

    sorted_data = []
    for k, v in sort_params(params):
        k = compat.encode_if_unicode(k)
        value = compat.encode_if_unicode(v)
        sorted_data.append((k, value))

    encoded = urlencode(sorted_data)
    hmac = sign(secret, params, url=url, method=method)

    return "%s&hmac=%s" % (encoded, hmac)


def sign_get_url(secret, url, signature_paramname="hmac"):  # pragma: no cover
    """
    Deprecated.

    Sign a URL to be GET-ed.

    This function takes a URL, parses it, sorts the URL parameters in
    alphabetical order, concatenates them with the character "&" inbetween and
    subsequently creates an HMAC using the secret key in ``hmac_key``.

    It then appends the signature in hex encoding in its own URL parameter,
    specified by ``signature_paramname`` and returns the resulting URL.

    This function is used for redirecting back to the merchant's page after a
    call to /identify or /gettoken

    :param secret: the secret key used to sign the URL
    :type secret: str
    :param url: the URL to sign
    :type url: str
    :param signature_paramname: the parameter name to append to ``url`` that
                                will contain the signature (default: "hmac")
    :type signature_paramname: str
    :returns: ``str`` -- the URL, including the signature as an URL parameter
    """
    warnings.warn(
        "sign_get_url is deprecated. It will be removed in a future release. "
        "It wasn't intended for public use. It's recommended to use the core "
        "signing API which is sign() and verify().",
        DeprecationWarning,
    )

    parsed = urlparse(url)

    if parsed.query != "":
        # use parse_qsl, because .parse_qs seems to create problems
        # with urlencode()
        qs = parse_qsl(parsed.query, keep_blank_values=True)

        # create string to sign

        # .sort() will sort in alphabetical order
        qs.append(("ts", str(int(time.time()))))
        qs.sort()

        hmac = sign(str(secret), qs, url, method="GET")

        qs.append((signature_paramname, hmac))
        return parsed.scheme + "://" + parsed.netloc + parsed.path + \
            parsed.params + "?" + urlencode(qs) + parsed.fragment

    return None
