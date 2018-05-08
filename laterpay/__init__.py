#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The LaterPay API Python client.

http://docs.laterpay.net/
"""

import collections
import logging
import pkg_resources
import random
import re
import string
import time
import warnings

import jwt
import requests

import six
from six.moves.urllib.parse import quote_plus

from . import compat, constants, signing, utils


_logger = logging.getLogger(__name__)

_PRICING_RE = re.compile(r'[A-Z]{3}\d+')
_EXPIRY_RE = re.compile(r'^(\+?\d+)$')
_SUB_ID_RE = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')


class InvalidTokenException(Exception):
    """
    Raised when a user's token is invalid (e.g. due to timeout).

    This exception is deprecated and will not be raised anymore.
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

    For PPU purchases: http://docs.laterpay.net/platform/dialogs/add/
    For Single item purchases: http://docs.laterpay.net/platform/dialogs/buy/
    """

    def __init__(self, item_id, pricing, url, title, expiry=None, sub_id=None,
                 period=None, item_type=None, election_id=None):
        for price in pricing.split(','):
            if not _PRICING_RE.match(price):
                raise InvalidItemDefinition('Pricing is not valid: %s' % pricing)

        if expiry is not None and not _EXPIRY_RE.match(expiry):
            raise InvalidItemDefinition("Invalid expiry value %s, it should be '+3600' or UTC-based "
                                        "epoch timestamp in seconds of type int" % expiry)

        self.data = {
            'pricing': pricing,
            'url': url,
            'title': title,
            'expiry': expiry,
        }

        if item_type in {
            constants.ITEM_TYPE_CONTRIBUTION,
            constants.ITEM_TYPE_DONATION,
            constants.ITEM_TYPE_POLITICAL_CONTRIBUTION,
        }:
            self.data['campaign_id'] = item_id
            self.item_type = item_type

            if item_type == constants.ITEM_TYPE_POLITICAL_CONTRIBUTION:
                self.data['election_id'] = election_id
        else:
            self.data['article_id'] = item_id
            self.item_type = None

        if sub_id is not None:
            if _SUB_ID_RE.match(sub_id):
                self.data['sub_id'] = sub_id
            else:
                raise InvalidItemDefinition(
                    "Invalid sub_id value '%s'. It can be any string consisting of lowercase or "
                    "uppercase ASCII characters, digits, underscore and hyphen, the length of "
                    "which is between 1 and 128 characters." % sub_id
                )
            if isinstance(period, int):
                self.data['period'] = period
            else:
                raise InvalidItemDefinition(
                    "Period not set or invalid value '%s'. The subscription period "
                    "must be an int in the range [3600, 31536000] (including)." % period,
                )


class LaterPayClient(object):

    def __init__(self,
                 cp_key,
                 shared_secret,
                 api_root='https://api.laterpay.net',
                 web_root='https://web.laterpay.net',
                 lptoken=None,
                 timeout_seconds=10,
                 connection_handler=None):
        """
        Instantiate a LaterPay API client.

        Defaults connecting to the production API.

        http://docs.laterpay.net/

        :param timeout_seconds: number of seconds after which backend api
            requests (e.g. /access) will time out (10 by default).
        :param connection_handler: Defaults to Python requests. Set it to
            ``requests.Session()`` to use a `Python requests Session object
            <http://docs.python-requests.org/en/master/user/advanced/#session-objects>`_.

        """
        self.cp_key = cp_key
        self.api_root = api_root
        self.web_root = web_root
        self.shared_secret = shared_secret
        self.lptoken = lptoken
        self.timeout_seconds = timeout_seconds
        self.connection_handler = connection_handler or requests

    def get_gettoken_redirect(self, return_to):
        """
        Get a URL from which a user will be issued a LaterPay token.

        http://docs.laterpay.net/platform/identification/gettoken/
        """
        url = self._gettoken_url
        data = {
            'redir': return_to,
            'cp': self.cp_key,
        }
        return utils.signed_url(self.shared_secret, data, url, method='GET')

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

        http://docs.laterpay.net/platform/inpage/login/
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

        data['xdmprefix'] = "".join(random.choice(string.ascii_letters) for x in range(10))

        url = '%s/controls/links' % self.web_root

        return utils.signed_url(self.shared_secret, data, url, method='GET')

    def get_controls_balance_url(self, forcelang=None):
        """
        Get the URL for an iframe showing the user's invoice balance.

        http://docs.laterpay.net/platform/inpage/balance/#get-controls-balance
        """
        data = {'cp': self.cp_key}
        if forcelang is not None:
            data['forcelang'] = forcelang
        data['xdmprefix'] = "".join(random.choice(string.ascii_letters) for x in range(10))

        base_url = "{web_root}/controls/balance".format(web_root=self.web_root)

        return utils.signed_url(self.shared_secret, data, base_url, method='GET')

    def get_login_dialog_url(self, next_url, use_jsevents=False):
        """Get the URL for a login page."""
        url = '%s/account/dialog/login?next=%s%s%s' % (
            self.web_root,
            quote_plus(next_url),
            "&jsevents=1" if use_jsevents else "",
            "&cp=%s" % self.cp_key,
        )
        return url

    def get_signup_dialog_url(self, next_url, use_jsevents=False):
        """Get the URL for a signup page."""
        url = '%s/account/dialog/signup?next=%s%s%s' % (
            self.web_root,
            quote_plus(next_url),
            "&jsevents=1" if use_jsevents else "",
            "&cp=%s" % self.cp_key,
        )
        return url

    def get_logout_dialog_url(self, next_url, use_jsevents=False):
        """Get the URL for a logout page."""
        url = '%s/account/dialog/logout?next=%s%s%s' % (
            self.web_root,
            quote_plus(next_url),
            "&jsevents=1" if use_jsevents else "",
            "&cp=%s" % self.cp_key,
        )
        return url

    @property
    def _access_url(self):
        return '%s/access' % self.api_root

    @property
    def _gettoken_url(self):
        return '%s/gettoken' % self.api_root

    def _get_web_url(self,
                     item_definition,
                     page_type,
                     product_key=None,
                     dialog=True,
                     use_jsevents=False,
                     transaction_reference=None,
                     consumable=False,
                     return_url=None,
                     failure_url=None,
                     muid=None,
                     is_permalink=False,
                     **kwargs):

        # filter out params with None value.
        data = {
            k: v
            for k, v
            in six.iteritems(item_definition.data)
            if v is not None
        }
        data['cp'] = self.cp_key

        if product_key is not None:
            data['product'] = product_key

        if dialog:
            prefix = '%s/%s' % (self.web_root, 'dialog')
        else:
            prefix = self.web_root

        if use_jsevents:
            data['jsevents'] = 1

        if transaction_reference:
            if len(transaction_reference) < 6:
                raise APIException('Transaction reference is not unique enough')
            data['tref'] = transaction_reference

        if consumable:
            data['consumable'] = 1

        if return_url:
            data['return_url'] = return_url

        if failure_url:
            data['failure_url'] = failure_url

        if muid:
            data['muid'] = muid

        data.update(kwargs)

        base_url = "%s/%s" % (prefix, page_type)

        return utils.signed_url(
            self.shared_secret,
            data,
            base_url,
            method='GET',
            is_permalink=is_permalink,
        )

    def get_buy_url(self, item_definition, *args, **kwargs):
        """
        Get the URL at which a user can start the checkout process.

        The created URL is a "pay_now" link for a single item, timepass,
        contribution, or donations.

        http://docs.laterpay.net/platform/dialogs/buy/
        """
        item_type = item_definition.item_type
        if item_type == constants.ITEM_TYPE_CONTRIBUTION:
            page_type = 'contribute/pay_now'
        elif item_type == constants.ITEM_TYPE_DONATION:
            page_type = 'donate/pay_now'
        elif item_type == constants.ITEM_TYPE_POLITICAL_CONTRIBUTION:
            page_type = 'political_contribution/pay_now'
        else:
            page_type = 'buy'

        return self._get_web_url(item_definition, page_type, *args, **kwargs)

    def get_add_url(self, item_definition, *args, **kwargs):
        """
        Get the URL at which a user can start the checkout process.

        The created URL is a "pay_later" link for a single item, timepass,
        contribution, or donations.

        http://docs.laterpay.net/platform/dialogs/add/
        """
        item_type = item_definition.item_type
        if item_type == constants.ITEM_TYPE_CONTRIBUTION:
            page_type = 'contribute/pay_later'
        elif item_type == constants.ITEM_TYPE_DONATION:
            page_type = 'donate/pay_later'
        elif item_type == constants.ITEM_TYPE_POLITICAL_CONTRIBUTION:
            page_type = 'political_contribution/pay_later'
        else:
            page_type = 'add'

        return self._get_web_url(item_definition, page_type, *args, **kwargs)

    def get_subscribe_url(self, item_definition, *args, **kwargs):
        """
        Get the URL at which a user can subscribe to an item.

        http://docs.laterpay.net/platform/dialogs/subscribe/
        """
        return self._get_web_url(item_definition, 'subscribe', *args, **kwargs)

    def has_token(self):
        """
        Do we have an identifier token.

        http://docs.laterpay.net/platform/identification/gettoken/
        """
        return self.lptoken is not None

    def get_request_headers(self):
        """
        Return a ``dict`` of request headers to be sent to the API.
        """
        version = pkg_resources.get_distribution('laterpay-client').version
        return {
            'X-LP-APIVersion': '2',
            'User-Agent': 'LaterPay Client Python v%s' % version,
        }

    def get_access_url(self):
        """
        Return the base url for /access endpoint.

        Example: https://api.laterpay.net/access
        """
        return self._access_url

    def get_access_params(self, article_ids, lptoken=None, muid=None):
        """
        Return a params ``dict`` for /access call.

        A correct signature is included in the dict as the "hmac" param.

        :param article_ids: Iterable of article ids or a single article id as a
                            string
        :param lptoken: optional lptoken as `str`
        :param str muid: merchant defined user ID. Optional.
        """
        if isinstance(article_ids, (six.text_type, six.binary_type)):
            article_ids = [article_ids]
        elif isinstance(article_ids, collections.Iterable):
            article_ids = list(sorted(article_ids))
        else:
            warnings.warn(
                'laterpay.LaterPayClient.get_access_params expects a string or '
                'a subclass of collections.Iterable as `article_ids`. Received '
                'a %r instead.' % type(article_ids),
                DeprecationWarning
            )
            article_ids = [article_ids]

        params = {
            'cp': self.cp_key,
            'ts': str(int(time.time())),
            'article_id': article_ids,
        }

        """
        Matrix on which combinations of `lptoken`, `muid`, and `self.lptoken`
        are allowed. In words:

            * Exactly one of `lptoken` and `muid`
            * If neither is given, but `self.lptoken` exists, use that

        l = lptoken
        s = self.lptoken
        m = muid
        x = error

               |   s   | not s |   s   | not s
        -------+-------+-------+-------+-------
           l   |   x   |   x   |   l   |   l
        -------+-------+-------+-------+-------
         not l |   m   |   m   |   s   |   x
        -------+-------+-------+-------+-------
               |   m   |   m   | not m | not m
        """
        if lptoken is None and muid is not None:
            params['muid'] = muid
        elif lptoken is not None and muid is None:
            params['lptoken'] = lptoken
        elif lptoken is None and muid is None and self.lptoken is not None:
            params['lptoken'] = self.lptoken
        else:
            raise AssertionError(
                'Either lptoken, self.lptoken or muid has to be passed. '
                'Passing neither or both lptoken and muid is not allowed.',
            )

        params['hmac'] = signing.sign(
            secret=self.shared_secret,
            params=params.copy(),
            url=self.get_access_url(),
            method='GET',
        )

        return params

    def get_access_data(self, article_ids, lptoken=None, muid=None):
        """
        Perform a request to /access API and return obtained data.

        This method uses ``requests.get`` or ``requests.Session().get`` to
        fetch the data and then calls ``.raise_for_status()`` on the response.
        It does not handle any errors raised by ``requests`` API.

        :param article_ids: Iterable of article ids or a single article id as a
                            string
        :param lptoken: optional lptoken as `str`
        :param str muid: merchant defined user ID. Optional.
        """
        params = self.get_access_params(article_ids=article_ids, lptoken=lptoken, muid=muid)
        url = self.get_access_url()
        headers = self.get_request_headers()

        response = self.connection_handler.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        return response.json()

    def get_manual_ident_url(self, article_url, article_ids, muid=None):
        """
        Return a URL to allow users to claim previous purchase content.
        """
        token = self._get_manual_ident_token(article_url, article_ids, muid=muid)
        return '%s/ident/%s/%s/' % (self.web_root, self.cp_key, token)

    def _get_manual_ident_token(self, article_url, article_ids, muid=None):
        """
        Return the token data for ``get_manual_ident_url()``.
        """
        data = {
            'back': compat.stringify(article_url),
            'ids': [compat.stringify(article_id) for article_id in article_ids],
        }
        if muid:
            data['muid'] = compat.stringify(muid)
        return jwt.encode(data, self.shared_secret).decode()
