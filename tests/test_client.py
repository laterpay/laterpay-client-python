#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys
import uuid

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from furl import furl

from laterpay.compat import urlparse, parse_qs
from laterpay import (
    APIException,
    InvalidItemDefinition,
    ItemDefinition,
    LaterPayClient,
)


class TestItemDefinition(unittest.TestCase):

    def test_item_definition(self):
        with self.assertRaises(InvalidItemDefinition):
            ItemDefinition(1, '', '', 'title')
        with self.assertRaises(InvalidItemDefinition):
            ItemDefinition(1, 'EUR20', 'http://foo.invalid', 'title', expiry="illegal123")

        it = ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', expiry='+100')

        self.assertEqual(it.data, {
            'article_id': 1,
            'cp': None,
            'expiry': '+100',
            'pricing': 'EUR20',
            'title': 'title',
            'url': 'http://example.com/t',
        })


class TestLaterPayClient(unittest.TestCase):

    def setUp(self):
        self.lp = LaterPayClient(
            1,
            'some-secret')
        self.item = ItemDefinition(1, 'EUR20', 'http://example.com/', 'title')

    def get_qs_dict(self, url):
        o = urlparse(url)
        d = parse_qs(o.query)
        o = urlparse(d['url'][0])
        d = parse_qs(o.query)
        return d

    def get_dialog_api_furl(self, url):
        return furl(furl(url).query.params['url'])

    def assertQueryString(self, url, key, value=None):
        d = self.get_qs_dict(url)
        if not value:
            return (key in d)
        return d.get(key, None) == value

    def test_transaction_reference(self):

        item = ItemDefinition(1, 'EUR20', 'http://foo.invalid', 'title')

        _u = str(uuid.uuid4())

        url = self.lp.get_add_url(
            item,
            product_key=123,
            dialog=True,
            use_jsevents=True,
            transaction_reference=_u)

        self.assertQueryString(url, 'tref', value=_u)

        url = self.lp.get_add_url(
            item,
            product_key=123,
            dialog=True,
            use_jsevents=True)

        d = self.get_qs_dict(url)
        self.assertFalse('tref' in d)

        with self.assertRaises(APIException):

            self.lp.get_add_url(
                item,
                product_key=123,
                dialog=True,
                use_jsevents=True,
                transaction_reference='123')

    def test_get_web_url_has_no_none_params(self):
        # item with expiry not set.
        item = ItemDefinition(1, 'EUR20', 'http://help.me/', 'title')
        url = self.lp.get_add_url(item)
        self.assertFalse(
            'expiry%3DNone' in url,
            'expiry url param is "None". Should be omitted.',
        )

    def test_failure_url_param(self):
        item = ItemDefinition(1, 'EUR20', 'http://help.me/', 'title')
        url = self.lp.get_add_url(item, failure_url="http://example.com")
        self.assertTrue('failure_url' in url)

        url = self.lp.get_buy_url(item, failure_url="http://example.com")
        self.assertTrue('failure_url' in url)

    def test_get_add_url_product_key_param(self):
        """
        Assert that `.get_add_url()` produces a "/dialog/add" url with
        `product_key` "product" query param.
        """
        url = self.lp.get_add_url(self.item, product_key="hopes")
        data = self.get_qs_dict(url)
        self.assertEqual(data['product'], ['hopes'])
        self.assertEqual(
            str(self.get_dialog_api_furl(url).path),
            '/dialog/add',
        )

    def test_get_buy_url_product_key_param(self):
        """
        Assert that `.get_buy_url()` produces a "/dialog/buy" url with
        `product_key` "product" query param.
        """
        url = self.lp.get_buy_url(self.item, product_key="hopes")
        data = self.get_qs_dict(url)
        self.assertEqual(data['product'], ['hopes'])
        self.assertEqual(
            str(self.get_dialog_api_furl(url).path),
            '/dialog/buy',
        )

    def test_get_add_url_no_product_key_param(self):
        """
        Assert that `.get_add_url()` produces a "/dialog/buy" url without
        "product" query param when no `product_key` method param is used.
        """
        url = self.lp.get_add_url(self.item)
        data = self.get_qs_dict(url)
        self.assertNotIn('product', data)
        self.assertEqual(
            str(self.get_dialog_api_furl(url).path),
            '/dialog/add',
        )

    def test_get_buy_url_no_product_key_param(self):
        """
        Assert that `.get_buy_url()` produces a "/dialog/buy" url without
        "product" query param when no `product_key` method param is used.
        """
        url = self.lp.get_buy_url(self.item)
        data = self.get_qs_dict(url)
        self.assertNotIn('product', data)
        self.assertEqual(
            str(self.get_dialog_api_furl(url).path),
            '/dialog/buy',
        )

    def test_get_buy_url_with_use_dialog_api_false(self):
        """
        Assert that `.get_buy_url()` returns a direct buy url, with no
        dialog-api iframe, when `use_dialog_api=False`
        """
        url = self.lp.get_buy_url(self.item, use_dialog_api=False)
        self.assertEqual(str(furl(url).path), '/dialog/buy')

    def test_get_add_url_with_use_dialog_api_false(self):
        """
        Assert that `.get_add_url()` returns a direct add url, with no
        dialog-api iframe, when `use_dialog_api=False`
        """
        url = self.lp.get_add_url(self.item, use_dialog_api=False)
        self.assertEqual(str(furl(url).path), '/dialog/add')

    def test_get_login_dialog_url_with_use_dialog_api_false(self):
        """
        Assert that `.get_login_dialog_url()` returns a url with no
        dialog-api iframe, when `use_dialog_api=False`
        """
        url = self.lp.get_login_dialog_url('http://example.org',
                                           use_dialog_api=False)
        self.assertEqual(str(furl(url).path), '/account/dialog/login')

    def test_get_login_dialog_url_without_use_dialog_api(self):
        """
        Assert that `.get_login_dialog_url()` returns a url with no
        dialog-api iframe, when `use_dialog_api` is not set (default)
        """
        url = self.lp.get_login_dialog_url('http://example.org')
        self.assertEqual(str(furl(url).path), '/dialog-api')

    def test_get_logout_dialog_url_with_use_dialog_api_false(self):
        """
        Assert that `.get_logout_dialog_url()` returns a url with no
        dialog-api iframe, when `use_dialog_api=False`
        """
        url = self.lp.get_logout_dialog_url('http://example.org',
                                            use_dialog_api=False)
        self.assertEqual(str(furl(url).path), '/account/dialog/logout')

    def test_get_logout_dialog_url_without_use_dialog_api(self):
        """
        Assert that `.get_logout_dialog_url()` returns a url with no
        dialog-api iframe, when `use_dialog_api` is not set (default)
        """
        url = self.lp.get_logout_dialog_url('http://example.org')
        self.assertEqual(str(furl(url).path), '/dialog-api')

    def test_get_signup_dialog_url_with_use_dialog_api_false(self):
        """
        Assert that `.get_signup_dialog_url()` returns a url with no
        dialog-api iframe, when `use_dialog_api=False`
        """
        url = self.lp.get_signup_dialog_url('http://example.org',
                                            use_dialog_api=False)
        self.assertEqual(str(furl(url).path), '/account/dialog/signup')

    def test_get_signup_dialog_url_without_use_dialog_api(self):
        """
        Assert that `.get_signup_dialog_url()` returns a url with no
        dialog-api iframe, when `use_dialog_api` is not set (default)
        """
        url = self.lp.get_signup_dialog_url('http://example.org')
        self.assertEqual(str(furl(url).path), '/dialog-api')


if __name__ == '__main__':
    unittest.main()
