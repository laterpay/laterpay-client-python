#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The LaterPay API Python client.

https://www.laterpay.net/developers/docs
"""

from __future__ import absolute_import, print_function

import json
import logging
import random
import re
import string

from . import signing
from . import compat

import warnings


_logger = logging.getLogger(__name__)


class InvalidTokenException(Exception):
    """
    Raised when a user's token is invalid (e.g. due to timeout).

    https://www.laterpay.net/developers/docs/backend-api#Invalidtokens
    """


class InvalidItemDefinition(Exception):
    """
    Raised when attempting to construct an `ItemDefinition` with invalid data.
    """


class APIException(Exception):
    """
    This will be deprecated in a future release.

    It is currently only raised when attempting to get a web URL with an
    insufficiently unique transaction reference. Expect this to be replaced with a
    more specific and helpfully named Exception.
    """


class ItemDefinition(object):
    """
    Contains data about content being sold through LaterPay.

    Documentation for usage:

    For PPU purchases: https://laterpay.net/developers/docs/dialog-api#GET/dialog/add
    For Single item purchases: https://laterpay.net/developers/docs/dialog-api#GET/dialog/buy
    """

    def __init__(self, item_id, pricing, url, title, cp=None, expiry=None):

        for price in pricing.split(','):
            if not re.match('[A-Z]{3}\d+', price):
                raise InvalidItemDefinition('Pricing is not valid: %s' % pricing)

        if expiry is not None and not re.match('^(\+?\d+)$', expiry):
            raise InvalidItemDefinition("Invalid expiry value %s, it should be '+3600' or UTC-based "
                                        "epoch timestamp in seconds of type int" % expiry)

        if cp is not None:
            warnings.warn("ItemDefinition's cp parameter is deprecated and will be ignored.", DeprecationWarning)

        self.data = {
            'article_id': item_id,
            'pricing': pricing,
            'url': url,
            'title': title,
            'expiry': expiry,
        }


class LaterPayClient(object):

    def __init__(self,
                 cp_key,
                 shared_secret,
                 api_root='https://api.laterpay.net',
                 web_root='https://web.laterpay.net',
                 lptoken=None,
                 timeout_seconds=10):
        """
        Instantiate a LaterPay API client.

        Defaults connecting to the production API.

        https://www.laterpay.net/developers/docs

        :param timeout_seconds: number of seconds after which backend api
            requests (e.g. /access) will time out (10 by default).

        """
        self.cp_key = cp_key
        self.api_root = api_root
        self.web_root = web_root
        self.shared_secret = shared_secret
        self.lptoken = lptoken
        self.timeout_seconds = timeout_seconds

    def get_gettoken_redirect(self, return_to):
        """
        Get a URL from which a user will be issued a LaterPay token.

        https://www.laterpay.net/developers/docs/backend-api#GET/gettoken
        """
        url = self._gettoken_url
        data = {
            'redir': return_to,
            'cp': self.cp_key,
        }
        params = self._sign_and_encode(
            params=data,
            url=url,
            method="GET",
        )
        url = '%s?%s' % (url, params)

        return url

    def get_identify_url(self, identify_callback=None):
        base_url = self._identify_url
        data = {'cp': self.cp_key}

        if identify_callback is not None:
            data['callback_url'] = identify_callback

        params = self._sign_and_encode(data, url=base_url, method="GET")
        url = '%s?%s' % (base_url, params)

        return url

    def get_iframeapi_links_url(self,
                                next_url,
                                css_url=None,
                                forcelang=None,
                                show_greeting=False,
                                show_long_greeting=False,
                                show_login=False,
                                show_signup=False,
                                show_long_signup=False,
                                use_jsevents=False):
        """ Deprecated, see get_controls_links_url. """
        warnings.warn("get_iframe_links_url is deprecated. Please use get_controls_links_url. "
                      "It will be removed on a future release.", DeprecationWarning)
        return self.get_controls_links_url(next_url, css_url, forcelang, show_greeting, show_long_greeting,
                                           show_login, show_signup, show_long_signup, use_jsevents)

    def get_controls_links_url(self,
                               next_url,
                               css_url=None,
                               forcelang=None,
                               show_greeting=False,
                               show_long_greeting=False,
                               show_login=False,
                               show_signup=False,
                               show_long_signup=False,
                               use_jsevents=False):
        """
        Get the URL for an iframe showing LaterPay account management links.

        https://www.laterpay.net/developers/docs/inpage-api#GET/controls/links
        """
        data = {'next': next_url}
        data['cp'] = self.cp_key
        if forcelang is not None:
            data['forcelang'] = forcelang
        if css_url is not None:
            data['css'] = css_url
        if use_jsevents:
            data['jsevents'] = "1"
        if show_long_greeting:
            data['show'] = '%sgg' % data.get('show', '')
        elif show_greeting:
            data['show'] = '%sg' % data.get('show', '')
        if show_login:
            data['show'] = '%sl' % data.get('show', '')
        if show_long_signup:
            data['show'] = '%sss' % data.get('show', '')
        elif show_signup:
            data['show'] = '%ss' % data.get('show', '')

        data['xdmprefix'] = "".join(random.choice(string.ascii_letters) for x in xrange(10))

        url = '%s/controls/links' % self.web_root
        params = self._sign_and_encode(data, url, method="GET")

        return '%s?%s' % (url, params)

    def get_iframeapi_balance_url(self, forcelang=None):
        """ Deprecated, see get_controls_balance_url. """
        warnings.warn("get_iframe_balance_url is deprecated. Please use get_controls_balance_url. "
                      "It will be removed on a future release.", DeprecationWarning)
        return self.get_controls_balance_url(forcelang)

    def get_controls_balance_url(self, forcelang=None):
        """
        Get the URL for an iframe showing the user's invoice balance.

        https://www.laterpay.net/developers/docs/inpage-api#GET/controls/balance
        """
        data = {'cp': self.cp_key}
        if forcelang is not None:
            data['forcelang'] = forcelang
        data['xdmprefix'] = "".join(random.choice(string.ascii_letters) for x in xrange(10))

        base_url = "{web_root}/controls/balance".format(web_root=self.web_root)
        encoded_data = self._sign_and_encode(data, base_url)
        url = "{base_url}?{encoded_data}".format(base_url=base_url, encoded_data=encoded_data)
        return url

    def _get_dialog_api_url(self, url):
        return '%s/dialog-api?url=%s' % (self.web_root, compat.quote_plus(url))

    def get_login_dialog_url(self, next_url, use_jsevents=False, use_dialog_api=True):
        """ Get the URL for a login page. """
        url = '%s/account/dialog/login?next=%s%s%s' % (self.web_root, compat.quote_plus(next_url),
                                                       "&jsevents=1" if use_jsevents else "",
                                                       "&cp=%s" % self.cp_key)
        if use_dialog_api:
            warnings.warn("The Dialog API Wrapper is deprecated and no longer recommended. "
                          "Please set use_dialog_api to False when calling get_login_dialog_url. "
                          "Future releases will not use the Dialog API Wrapper by default. "
                          "See http://docs.laterpay.net/platform/dialogs/third_party_cookies/",
                          DeprecationWarning)
            return self._get_dialog_api_url(url)
        return url

    def get_signup_dialog_url(self, next_url, use_jsevents=False, use_dialog_api=True):
        """ Get the URL for a signup page. """
        url = '%s/account/dialog/signup?next=%s%s%s' % (self.web_root, compat.quote_plus(next_url),
                                                        "&jsevents=1" if use_jsevents else "",
                                                        "&cp=%s" % self.cp_key)
        if use_dialog_api:
            warnings.warn("The Dialog API Wrapper is deprecated and no longer recommended. "
                          "Please set use_dialog_api to False when calling get_signup_dialog_url. "
                          "Future releases will not use the Dialog API Wrapper by default. "
                          "See http://docs.laterpay.net/platform/dialogs/third_party_cookies/",
                          DeprecationWarning)
            return self._get_dialog_api_url(url)
        return url

    def get_logout_dialog_url(self, next_url, use_jsevents=False, use_dialog_api=True):
        """ Get the URL for a logout page. """
        url = '%s/account/dialog/logout?next=%s%s%s' % (self.web_root, compat.quote_plus(next_url),
                                                        "&jsevents=1" if use_jsevents else "",
                                                        "&cp=%s" % self.cp_key)
        if use_dialog_api:
            warnings.warn("The Dialog API Wrapper is deprecated and no longer recommended. "
                          "Please set use_dialog_api to False when calling get_logout_dialog_url. "
                          "Future releases will not use the Dialog API Wrapper by default. "
                          "See http://docs.laterpay.net/platform/dialogs/third_party_cookies/",
                          DeprecationWarning)
            return self._get_dialog_api_url(url)
        return url

    @property
    def _access_url(self):
        return '%s/access' % self.api_root

    @property
    def _add_url(self):
        return '%s/add' % self.api_root

    @property
    def _identify_url(self):
        return '%s/identify' % self.api_root

    @property
    def _gettoken_url(self):
        return '%s/gettoken' % self.api_root

    def _get_web_url(self,
                     item_definition,
                     page_type,
                     product_key=None,
                     dialog=True,
                     use_jsevents=False,
                     skip_add_to_invoice=False,
                     transaction_reference=None,
                     consumable=False,
                     return_url=None,
                     failure_url=None,
                     use_dialog_api=True):

        # filter out params with None value.
        data = {k: v for k, v in item_definition.data.items() if v is not None}
        data['cp'] = self.cp_key

        if use_jsevents:
            data['jsevents'] = 1

        if consumable:
            data['consumable'] = 1

        if return_url:
            data['return_url'] = return_url

        if failure_url:
            data['failure_url'] = failure_url

        if transaction_reference:

            if len(transaction_reference) < 6:
                raise APIException('Transaction reference is not unique enough')

            data['tref'] = transaction_reference

        if skip_add_to_invoice:
            data['skip_add_to_invoice'] = 1

        if dialog:
            prefix = '%s/%s' % (self.web_root, 'dialog')
        else:
            prefix = self.web_root

        if product_key is not None:
            data['product'] = product_key

        base_url = "%s/%s" % (prefix, page_type)

        params = self._sign_and_encode(data, base_url, method="GET")
        url = "{base_url}?{params}".format(base_url=base_url, params=params)

        if use_dialog_api:
            warnings.warn("The Dialog API Wrapper is deprecated and no longer recommended. "
                          "Please set use_dialog_api to False when calling get_buy_url or get_add_url. "
                          "Future releases will not use the Dialog API Wrapper by default. "
                          "See http://docs.laterpay.net/platform/dialogs/third_party_cookies/",
                          DeprecationWarning)
            return self._get_dialog_api_url(url)
        return url

    def get_buy_url(self,
                    item_definition,
                    product_key=None,
                    dialog=True,
                    use_jsevents=False,
                    skip_add_to_invoice=False,
                    transaction_reference=None,
                    consumable=False,
                    return_url=None,
                    failure_url=None,
                    use_dialog_api=True):
        """
        Get the URL at which a user can start the checkout process to buy a single item.

        https://www.laterpay.net/developers/docs/dialog-api#GET/dialog/buy
        """
        return self._get_web_url(
            item_definition,
            'buy',
            product_key=product_key,
            dialog=dialog,
            use_jsevents=use_jsevents,
            skip_add_to_invoice=skip_add_to_invoice,
            transaction_reference=transaction_reference,
            consumable=consumable,
            return_url=return_url,
            failure_url=failure_url,
            use_dialog_api=use_dialog_api)

    def get_add_url(self,
                    item_definition,
                    product_key=None,
                    dialog=True,
                    use_jsevents=False,
                    skip_add_to_invoice=False,
                    transaction_reference=None,
                    consumable=False,
                    return_url=None,
                    failure_url=None,
                    use_dialog_api=True):
        """
        Get the URL at which a user can add an item to their invoice to pay later.

        https://www.laterpay.net/developers/docs/dialog-api#GET/dialog/add
        """
        return self._get_web_url(
            item_definition,
            'add',
            product_key=product_key,
            dialog=dialog,
            use_jsevents=use_jsevents,
            skip_add_to_invoice=skip_add_to_invoice,
            transaction_reference=transaction_reference,
            consumable=consumable,
            return_url=return_url,
            failure_url=failure_url,
            use_dialog_api=use_dialog_api)

    def _sign_and_encode(self, params, url, method="GET"):
        return signing.sign_and_encode(self.shared_secret, params, url=url, method=method)

    def _make_request(self, url, params, method='GET'):

        params = self._sign_and_encode(params=params, url=url, method=method)

        headers = {
            'X-LP-APIVersion': 2,
            'User-Agent': 'LaterPay Client - Python - v0.2'
        }

        if method == 'POST':
            req = compat.Request(url, data=params, headers=headers)
        else:
            url = "%s?%s" % (url, params)
            req = compat.Request(url, headers=headers)

        _logger.debug("Making request to %s", url)

        try:
            response = compat.urlopen(req, timeout=self.timeout_seconds).read()
        except:
            # TODO: Add proper or no exception handling.
            # Pretending there was a response even if there was none
            # (can't connect / timeout) seems like a wrong idea.
            _logger.exception("Unexpected error with request")
            resp = {'status': 'unexpected error'}
        else:
            _logger.debug("Received response %s", response)
            resp = json.loads(response)

        if 'new_token' in resp:
            self.lptoken = resp['new_token']

        if resp.get('status', None) == 'invalid_token':
            self.lptoken = None

        return resp

    def has_token(self):
        """
        Do we have an identifier token.

        https://www.laterpay.net/developers/docs/backend-api#GET/gettoken
        """
        return self.lptoken is not None

    def get_access(self, article_ids, product_key=None):
        """
        Get access data for a set of article ids.

        https://www.laterpay.net/developers/docs/backend-api#GET/access
        """
        if not isinstance(article_ids, (list, tuple)):
            article_ids = [article_ids]

        params = {
            'lptoken': self.lptoken,
            'cp': self.cp_key,
            'article_id': article_ids
        }

        if product_key is not None:
            params['product'] = product_key

        data = self._make_request(self._access_url, params)

        allowed_statuses = ['ok', 'invalid_token', 'connection_error']

        if data['status'] not in allowed_statuses:
            raise Exception(data['status'])

        return data
