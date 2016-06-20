#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import json
import uuid
import unittest

import mock
import responses

from furl import furl
from six.moves.urllib.parse import urlparse, parse_qs

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

    def test_get_web_url_extra_kwargs(self):
        item = ItemDefinition(1, 'EUR20', 'http://example.net/t', 'title')
        url = self.lp.get_add_url(
            item,
            use_dialog_api=False,
            something_more=['x', 'y']
        )
        qd = parse_qs(urlparse(url).query)
        self.assertEqual(qd['something_more'], ['x', 'y'])

        url = self.lp.get_buy_url(
            item,
            use_dialog_api=False,
            something_more=['x', 'y']
        )
        qd = parse_qs(urlparse(url).query)
        self.assertEqual(qd['something_more'], ['x', 'y'])

    @mock.patch('laterpay.warnings.warn')
    def test_log_warning_for_skip_add_to_invoice_deprecation(self, warning_mock):
        item = ItemDefinition(1, 'EUR20', 'http://help.me/', 'title')
        self.lp.get_add_url(item, skip_add_to_invoice=True,
                            use_dialog_api=False)
        warning_mock.assert_called_once_with("The param skip_add_to_invoice is "
                                             "deprecated and it will be removed "
                                             "in a future release.",
                                             DeprecationWarning)

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

    @mock.patch('laterpay.signing.sign')
    @mock.patch('time.time')
    @responses.activate
    def test_get_access_data_success(self, time_time_mock, sign_mock):
        time_time_mock.return_value = 123
        sign_mock.return_value = 'fake-signature'
        responses.add(
            responses.GET,
            'http://example.net/access',
            body=json.dumps({
                "status": "ok",
                "articles": {
                    "article-1": {"access": True},
                    "article-2": {"access": False},
                },
            }),
            status=200,
            content_type='application/json',
        )

        client = LaterPayClient(
            'fake-cp-key',
            'fake-shared-secret',
            api_root='http://example.net',
        )

        data = client.get_access_data(
            ['article-1', 'article-2'],
            lptoken='fake-lptoken',
        )

        self.assertEqual(data, {
            "status": "ok",
            "articles": {
                "article-1": {"access": True},
                "article-2": {"access": False},
            },
        })
        self.assertEqual(len(responses.calls), 1)

        call = responses.calls[0]

        self.assertEqual(call.request.headers['X-LP-APIVersion'], 2)

        qd = parse_qs(urlparse(call.request.url).query)

        self.assertEqual(qd['ts'], ['123'])
        self.assertEqual(qd['lptoken'], ['fake-lptoken'])
        self.assertEqual(qd['cp'], ['fake-cp-key'])
        self.assertEqual(qd['article_id'], ['article-1', 'article-2'])
        self.assertEqual(qd['hmac'], ['fake-signature'])

        sign_mock.assert_called_once_with(
            secret='fake-shared-secret',
            params={
                'cp': 'fake-cp-key',
                'article_id': ['article-1', 'article-2'],
                'ts': '123',
                'lptoken': 'fake-lptoken',
            },
            url='http://example.net/access',
            method='GET',
        )

    @mock.patch('laterpay.signing.sign')
    @mock.patch('time.time')
    def test_get_access_params(self, time_time_mock, sign_mock):
        time_time_mock.return_value = 123
        sign_mock.return_value = 'fake-signature'

        params = self.lp.get_access_params('article-1', lptoken='fake-lptoken')

        self.assertEqual(params, {
            'cp': 1,
            'ts': '123',
            'lptoken': 'fake-lptoken',
            'article_id': ['article-1'],
            'hmac': 'fake-signature',
        })

    @mock.patch('time.time')
    def test_get_gettoken_redirect(self, time_mock):
        time_mock.return_value = 12345678

        gettoken_url = self.lp.get_gettoken_redirect(
            'http://example.com/token-here')

        scheme, netloc, path, _, query, _ = urlparse(gettoken_url)
        qd = parse_qs(query)

        self.assertEqual(scheme, 'https')
        self.assertEqual(netloc, 'api.laterpay.net')
        self.assertEqual(path, '/gettoken')

        self.assertEqual(set(qd.keys()), set(['cp', 'redir', 'ts', 'hmac']))
        self.assertEqual(qd['ts'], ['12345678'])
        self.assertEqual(qd['cp'], ['1'])
        self.assertEqual(qd['redir'], ['http://example.com/token-here'])
        self.assertEqual(
            qd['hmac'],
            ['4f59ae6601fc99e962297fb1db607caeeb8e841fee8f439b526c7f41'],
        )

    def test_has_token(self):
        client = LaterPayClient('cp-key', 'shared-secret')
        self.assertFalse(client.has_token())

        client = LaterPayClient('cp-key', 'shared-secret', lptoken='foo')
        self.assertTrue(client.has_token())

    @mock.patch('time.time', return_value=12345678)
    def test_get_controls_links_url_all_defaults(self, time_mock):
        signed_url = self.lp.get_controls_links_url('http://example.com/foo/?bar=buz')
        scheme, netloc, path, _, query, _ = urlparse(signed_url)
        query = parse_qs(query)
        self.assertEqual(scheme, 'https')
        self.assertEqual(netloc, 'web.laterpay.net')
        self.assertEqual(path, '/controls/links')
        del query['hmac']  # Ensures the key was set
        del query['xdmprefix']  # Ensures the key was set
        self.assertEqual(query, {
            'cp': ['1'],
            'next': ['http://example.com/foo/?bar=buz'],
            'ts': ['12345678'],
        })

    @mock.patch('time.time', return_value=12345678)
    def test_get_controls_links_url_all_set_short(self, time_mock):
        signed_url = self.lp.get_controls_links_url(
            'http://example.com/foo/?bar=buz',
            css_url='http://cdn.com/some.css',
            forcelang='de',
            show_greeting=True,
            show_login=True,
            show_signup=True,
            use_jsevents=True,
        )
        scheme, netloc, path, _, query, _ = urlparse(signed_url)
        query = parse_qs(query)
        self.assertEqual(scheme, 'https')
        self.assertEqual(netloc, 'web.laterpay.net')
        self.assertEqual(path, '/controls/links')
        del query['hmac']  # Ensures the key was set
        del query['xdmprefix']  # Ensures the key was set
        self.assertEqual(query, {
            'cp': ['1'],
            'css': ['http://cdn.com/some.css'],
            'forcelang': ['de'],
            'jsevents': ['1'],
            'next': ['http://example.com/foo/?bar=buz'],
            'show': ['gls'],
            'ts': ['12345678'],
        })

    @mock.patch('time.time', return_value=12345678)
    def test_get_controls_links_url_all_set_long(self, time_mock):
        signed_url = self.lp.get_controls_links_url(
            'http://example.com/foo/?bar=buz',
            css_url='http://cdn.com/some.css',
            forcelang='de',
            show_long_greeting=True,
            show_login=True,
            show_long_signup=True,
            use_jsevents=True,
        )
        scheme, netloc, path, _, query, _ = urlparse(signed_url)
        query = parse_qs(query)
        self.assertEqual(scheme, 'https')
        self.assertEqual(netloc, 'web.laterpay.net')
        self.assertEqual(path, '/controls/links')
        del query['hmac']  # Ensures the key was set
        del query['xdmprefix']  # Ensures the key was set
        self.assertEqual(query, {
            'cp': ['1'],
            'css': ['http://cdn.com/some.css'],
            'forcelang': ['de'],
            'jsevents': ['1'],
            'next': ['http://example.com/foo/?bar=buz'],
            'show': ['gglss'],
            'ts': ['12345678'],
        })

    @mock.patch('time.time', return_value=12345678)
    def test_get_controls_balance_url_all_defaults(self, time_mock):
        signed_url = self.lp.get_controls_balance_url()
        scheme, netloc, path, _, query, _ = urlparse(signed_url)
        query = parse_qs(query)
        self.assertEqual(scheme, 'https')
        self.assertEqual(netloc, 'web.laterpay.net')
        self.assertEqual(path, '/controls/balance')
        del query['hmac']  # Ensures the key was set
        del query['xdmprefix']  # Ensures the key was set
        self.assertEqual(query, {
            'cp': ['1'],
            'ts': ['12345678'],
        })

    @mock.patch('time.time', return_value=12345678)
    def test_get_controls_balance_url_all_set(self, time_mock):
        signed_url = self.lp.get_controls_balance_url(forcelang='de')
        scheme, netloc, path, _, query, _ = urlparse(signed_url)
        query = parse_qs(query)
        self.assertEqual(scheme, 'https')
        self.assertEqual(netloc, 'web.laterpay.net')
        self.assertEqual(path, '/controls/balance')
        del query['hmac']  # Ensures the key was set
        del query['xdmprefix']  # Ensures the key was set
        self.assertEqual(query, {
            'cp': ['1'],
            'forcelang': ['de'],
            'ts': ['12345678'],
        })


if __name__ == '__main__':
    unittest.main()
