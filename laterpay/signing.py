# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import functools
import hashlib
import hmac
import time

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
    authcode = hmac.new(compat.b(HMAC_secret), digestmod=hashlib.sha224)
    for part in parts:
        authcode.update(compat.b(part))
    return authcode.hexdigest()


def sort_params(param_dict):
    """
    Sort a key-value mapping with non-unique keys.

    This function should probably not be part of the public API, and thus will
    be deprecated in a future release to be replaced with a internal function.
    """
    def cmp_params(param1, param2):
        result = compat.cmp(param1[0], param2[0])
        if result == 0:
            result = compat.cmp(param1[1], param2[1])
        return result

    param_list = []
    for name, value_list in param_dict.items():
        if isinstance(value_list, (list, tuple)):
            for value in value_list:
                if not isinstance(value, compat.string_types):
                    value = str(value)
                param_list.append((name, value))
        else:
            if not isinstance(value_list, compat.string_types):
                value_list = str(value_list)
            param_list.append((name, value_list))

    if compat.py3k:
        return sorted(param_list, key=functools.cmp_to_key(cmp_params))
    return sorted(param_list, cmp_params)


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
    for key, value in params.items():
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

    See https://www.laterpay.net/developers/docs/start#SigningURLs for details
    """
    msg = '{method}&{url}&{params}'

    method = _encode_if_unicode(method).upper()

    data = {}

    url = compat.quote(_encode_if_unicode(url), safe='')

    if method not in ALLOWED_METHODS:
        raise ValueError('method should be one of: {}'.format(ALLOWED_METHODS))

    params = normalise_param_structure(params)

    for key, values in params.items():
        key = compat.quote(_encode_if_unicode(key), safe='')

        if not isinstance(values, (list, tuple)):
            values = [values]

        values_str = []

        # If any non compat.string_types objects, ``str()`` them.
        for value in values:
            if not isinstance(value, compat.string_types):
                value = str(value)
            values_str.append(value)

        data[key] = [compat.quote(_encode_if_unicode(value_str), safe='') for value_str in values_str]

    sorted_params = sort_params(data)

    param_str = '&'.join('{}={}'.format(k, v) for k, v in sorted_params)
    param_str = compat.quote(param_str, safe='')

    return msg.format(method=method, url=url, params=param_str)


def sign(secret, params, url, method='POST'):
    """
    Create signature for given `params`, `url` and HTTP method.

    How params are canonicalized:
    - `compat.quote` every key and value that will be signed
    - sort the param list
    - `'&'join` the params

    :param secret: Secret used to create signature
    :type secret: str/unicode
    :param params: Mapping of all params that should be signed.
        This includes url params as well as requests body params,
        regardless if body is 'application/x-www-form-urlencoded' or
        'application/json'.
    :type params: dict of unicode/str keys and values. Values can
        be a list/tuple of unicode/str.
    :param url: full url of the target endpoint, no url params
        (eg. https://host/api)
    :type url: str/unicode
    """
    if 'hmac' in params:
        params.pop('hmac')

    if 'gettoken' in params:
        params.pop('gettoken')

    secret = _encode_if_unicode(secret)

    url_parsed = compat.urlparse(url)
    base_url = url_parsed.scheme + "://" + url_parsed.netloc + url_parsed.path

    msg = create_base_message(params, base_url, method=method)

    mac = create_HMAC(secret, msg)

    return mac


def verify(signature, secret, params, url, method):
    """
    Verify the signature on a signed URL.

    Redirects back to a client's server from LaterPay will be signed to ensure
    authenticity. Use `verify` to confirm this.
    """
    if isinstance(signature, (list, tuple)):
        signature = signature[0]

    mac = sign(secret, params, url, method)

    return time_independent_HMAC_compare(signature, mac)


def sign_and_encode(secret, params, url, method="GET"):
    """
    Sign and encode a URL ``url`` with a ``secret`` key called via an HTTP ``method``.

    It adds the signature to the URL
    as the URL parameter "hmac" and also adds the required timestamp parameter "ts" if it's not already
    in the ``params`` dictionary. ``unicode()`` instances in params are handled correctly.

    :param secret: The shared secret as a hex-encoded string
    :param params: A dictionary of URL parameters. Each key can resolve to a single value string or a multi-string list.
    :param url: the URL being called
    :param method: an uppercase string representation of the HTTP method being used for the call (e.g. "GET", "POST")
    :return: a signed and correctly encoded URL
    """
    if 'ts' not in params:
        params['ts'] = str(int(time.time()))

    if 'hmac' in params:
        params.pop('hmac')

    sorted_data = []
    for k, v in sort_params(params):
        k = _encode_if_unicode(k)
        value = _encode_if_unicode(v)
        sorted_data.append((k, value))

    encoded = compat.urlencode(sorted_data)
    hmac = sign(secret, params, url=url, method=method)

    return "%s&hmac=%s" % (encoded, hmac)


def sign_get_url(secret, url, signature_paramname="hmac"):
    """
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
    parsed = compat.urlparse(url)

    if parsed.query != "":
        # use compat.parse_qsl, because .parse_qs seems to create problems
        # with compat.urlencode()
        qs = compat.parse_qsl(parsed.query, keep_blank_values=True)

        # create string to sign

        # .sort() will sort in alphabetical order
        qs.append(("ts", str(int(time.time()))))
        qs.sort()

        hmac = sign(str(secret), qs, url, method="GET")

        qs.append((signature_paramname, hmac))
        return parsed.scheme + "://" + parsed.netloc + parsed.path + \
            parsed.params + "?" + compat.urlencode(qs) + parsed.fragment

    return None


def _encode_if_unicode(value, encoding='utf-8'):
    """
    Encode and return a ``value`` using specified ``encoding``.

    Encoding is done only if ``value`` is a ``unicode`` instance
    (utf-8 encoding is used as default).

    This utility is needed because some web frameworks can provide
    request arguments as ``str`` instances.
    """
    if not compat.py3k and isinstance(value, unicode):
        value = value.encode(encoding)
    return value
