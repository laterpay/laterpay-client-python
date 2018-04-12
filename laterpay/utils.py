# -*- coding: utf-8 -*-
import time

from six.moves.urllib.parse import urlencode

from laterpay import signing


def signed_query(secret,
                 params,
                 url,
                 method="GET",
                 add_timestamp=True,
                 is_permalink=False,
                 signature_param_name="hmac"):
    """
    Create a signed and url-encoded query string from passed in ``params``.

    The params are signed using ``laterpay.signing.sign()`` and the signature
    is appended to the query as the ``signature_param_name`` param.

    A "ts" param containing current Unix timestamp will also be added to the
    query if ``add_timestamp`` is ``True`` (default) and there is no "ts" key
    in the ``params`` dict.

    :param secret: The shared secret
    :param params: A ``dict`` of URL parameters. Each value in this ``dict``
                   can be either a string or a list of strings.
    :param url: The base url (no params) passed to ``signing.sign()``.
                Example: "https://example.com/here"
    :param method: An uppercase string representation of the HTTP method passed
                   to ``signing.sign()``. "GET" is a default.
    :param add_timestamp: ``bool`` (default True) - Should a timestamp param be
                          added to the query.
    :param is_permalink: ``bool`` (default False) - Generate a permanent
                (non-expiring) link. If ``True``, ``add_timestamp`` will be
                ignored and a timestamp will not be added to the query.
    :param signature_param_name: Name of the appended signature param
                                 (default "hmac")

    :return: url-encoded and signed query string
    """
    params = signing.normalise_param_structure(params)

    if is_permalink:
        params["permalink"] = "1"
        if "ts" in params:
            params.pop("ts")
    elif "ts" not in params and add_timestamp:
        params["ts"] = str(int(time.time()))

    param_list = list(params.items())

    qs = urlencode(param_list, doseq=True)

    signature = signing.sign(secret, params, url=url, method=method)

    return "{}&{}={}".format(qs, signature_param_name, signature)


def signed_url(secret, params, url, **kwargs):
    """
    Return the same as ``signed_query`` but including the base URL.
    """
    qs = signed_query(secret, params, url, **kwargs)
    return "{}?{}".format(url, qs)
