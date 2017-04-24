#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
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

    def test_invalid_pricing(self):
        with self.assertRaises(InvalidItemDefinition):
            ItemDefinition(1, '', '', 'title')

    def test_invalid_expiry(self):
        with self.assertRaises(InvalidItemDefinition):
            ItemDefinition(1, 'EUR20', 'http://foo.invalid', 'title', expiry="illegal123")

    def test_invalid_sub_id(self):
        with self.assertRaisesRegexp(InvalidItemDefinition, r'^Invalid sub_id value '):
            ItemDefinition(1, 'EUR20', 'http://example.com', 'title', sub_id='', period=3600)
        with self.assertRaisesRegexp(InvalidItemDefinition, r'^Invalid sub_id value '):
            ItemDefinition(1, 'EUR20', 'http://example.com', 'title', sub_id='a' * 129, period=3600)
        with self.assertRaisesRegexp(InvalidItemDefinition, r'^Invalid sub_id value '):
            ItemDefinition(1, 'EUR20', 'http://example.com', 'title', sub_id='ä', period=3600)

    def test_invalid_period(self):
        with self.assertRaisesRegexp(InvalidItemDefinition, r'Period not set or invalid value'):
            ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', sub_id='a', period=60 * 60 - 1)
        with self.assertRaisesRegexp(InvalidItemDefinition, r'Period not set or invalid value'):
            ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', sub_id='a', period=60 * 60 * 24 * 31 * 12 + 1)
        with self.assertRaisesRegexp(InvalidItemDefinition, r'Period not set or invalid value'):
            ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', sub_id='a', period='12345')

    def test_item_definition(self):
        it = ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', expiry='+100')
        self.assertEqual(it.data, {
            'article_id': 1,
            'expiry': '+100',
            'pricing': 'EUR20',
            'title': 'title',
            'url': 'http://example.com/t',
        })

    def test_sub_id(self):
        # Test sub_id_bounds
        ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', sub_id='a', period=60 * 60)
        ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', sub_id='a' * 128, period=60 * 60 * 24 * 31 * 12)

        it = ItemDefinition(1, 'EUR20', 'http://example.com/t', 'title', sub_id='abc', period=12345)
        self.assertEqual(it.data, {
            'article_id': 1,
            'expiry': None,
            'period': 12345,
            'pricing': 'EUR20',
            'sub_id': 'abc',
            'title': 'title',
            'url': 'http://example.com/t',
        })


class TestLaterPayClient(unittest.TestCase):

    def setUp(self):
        self.lp = LaterPayClient(
            '1',
            'some-secret')
        self.item = ItemDefinition(1, 'EUR20', 'http://example.com/', 'title')

    def assertQueryString(self, url, key, value=None):
        d = parse_qs(urlparse(url).query)
        if not value:
            return (key in d)
        return d.get(key, None) == value

    def test_get_web_url_itemdefinition_value_none(self):
        # item with expiry not set.
        item = ItemDefinition(1, 'EUR20', 'http://help.me/', 'title')
        url = self.lp._get_web_url(item, 'PAGE_TYPE')
        self.assertFalse(
            self.assertQueryString(url, 'expiry'),
            'expiry url param is "None". Should be omitted.'
        )

    def test_web_url_product_key(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertFalse(self.assertQueryString(url, 'product_key'))

        # Enabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', product_key='foobar')
        self.assertQueryString(url, 'product_key', value='foobar')

        # Disabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', product_key=None)
        self.assertFalse(self.assertQueryString(url, 'product_key'))

    def test_web_url_dialog(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertTrue(url.startswith('https://web.laterpay.net/dialog/PAGE_TYPE?'))

        # Enabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', dialog=True)
        self.assertTrue(url.startswith('https://web.laterpay.net/dialog/PAGE_TYPE?'))

        # Disabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', dialog=False)
        self.assertTrue(url.startswith('https://web.laterpay.net/PAGE_TYPE?'))

    def test_web_url_jsevents(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertFalse(self.assertQueryString(url, 'jsevents'))

        # Enabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', use_jsevents=True)
        self.assertQueryString(url, 'jsevents', value='1')

        # Disabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', use_jsevents=False)
        self.assertFalse(self.assertQueryString(url, 'jsevents'))

    def test_web_url_transaction_reference(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertFalse(self.assertQueryString(url, 'transaction_reference'))

        # Valid
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', transaction_reference='loremipsum')
        self.assertQueryString(url, 'transaction_reference', value='loremipsum')

        # Invalid
        with self.assertRaises(APIException):
            self.lp._get_web_url(self.item, 'PAGE_TYPE', transaction_reference='foo')

    def test_web_url_consumable(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertFalse(self.assertQueryString(url, 'consumable'))

        # Enabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', consumable=True)
        self.assertQueryString(url, 'consumable', value='1')

        # Disabled
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', consumable=False)
        self.assertFalse(self.assertQueryString(url, 'consumable'))

    def test_web_url_return_url(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertFalse(self.assertQueryString(url, 'return_url'))

        # Given
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', return_url='http://example.com/foo?foo=bar&lorem=ipsum')
        self.assertQueryString(url, 'return_url', value='http://example.com/foo?foo=bar&lorem=ipsum')

        # Omitted
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', return_url=None)
        self.assertFalse(self.assertQueryString(url, 'return_url'))

    def test_web_url_failure_url(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertFalse(self.assertQueryString(url, 'failure_url'))

        # Given
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', failure_url='http://example.com/foo?foo=bar&lorem=ipsum')
        self.assertQueryString(url, 'failure_url', value='http://example.com/foo?foo=bar&lorem=ipsum')

        # Omitted
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', failure_url=None)
        self.assertFalse(self.assertQueryString(url, 'failure_url'))

    def test_web_url_muid(self):
        # Default
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE')
        self.assertFalse(self.assertQueryString(url, 'muid'))

        # Given
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', muid='0zA9-aZ09-0A9z')
        self.assertQueryString(url, 'muid', value='0zA9-aZ09-0A9z')

        # Omitted
        url = self.lp._get_web_url(self.item, 'PAGE_TYPE', muid=None)
        self.assertFalse(self.assertQueryString(url, 'muid'))

    def test_get_add_url(self):
        item = ItemDefinition(1, 'EUR20', 'http://example.net/t', 'title')
        url = self.lp.get_add_url(
            item,
            product_key='some-product-key',
            dialog=False,
            use_jsevents=True,
            transaction_reference='TX-REF',
            consumable=True,
            return_url='http://return.url/foo?bar=buz&lorem=ipsum',
            failure_url='http://failure.url/FOO?BAR=BUZ&LOREM=IPSUM',
            muid='someone',
            something='else',
            BLUB=[u'u2', b'b1', b'b2', u'u1'],
        )
        self.assertFalse(
            self.assertQueryString(url, 'expiry'),
            'expiry url param is "None". Should be omitted.'
        )
        self.assertQueryString(url, 'product_key', value='some-product-key')
        self.assertTrue(url.startswith('https://web.laterpay.net/add?'))
        self.assertQueryString(url, 'use_jsevents', value='1')
        self.assertQueryString(url, 'transaction_reference', value='TX-REF')
        self.assertQueryString(url, 'consumable', value='1')
        self.assertQueryString(url, 'return_url', value='http://return.url/foo?bar=buz&lorem=ipsum')
        self.assertQueryString(url, 'failure_url', value='http://failure.url/FOO?BAR=BUZ&LOREM=IPSUM')
        self.assertQueryString(url, 'muid', value='someone')
        self.assertQueryString(url, 'something', value='else')
        self.assertQueryString(url, 'BLUB', value=[b'b1', 'b2', u'u1', 'u2'])

    def test_get_buy_url(self):
        item = ItemDefinition(1, 'EUR20', 'http://example.net/t', 'title')
        url = self.lp.get_buy_url(
            item,
            product_key='some-product-key',
            dialog=False,
            use_jsevents=True,
            transaction_reference='TX-REF',
            consumable=True,
            return_url='http://return.url/foo?bar=buz&lorem=ipsum',
            failure_url='http://failure.url/FOO?BAR=BUZ&LOREM=IPSUM',
            muid='someone',
            something='else',
            BLUB=[u'u2', b'b1', b'b2', u'u1'],
        )
        self.assertFalse(
            self.assertQueryString(url, 'expiry'),
            'expiry url param is "None". Should be omitted.'
        )
        self.assertQueryString(url, 'product_key', value='some-product-key')
        self.assertTrue(url.startswith('https://web.laterpay.net/buy?'))
        self.assertQueryString(url, 'use_jsevents', value='1')
        self.assertQueryString(url, 'transaction_reference', value='TX-REF')
        self.assertQueryString(url, 'consumable', value='1')
        self.assertQueryString(url, 'return_url', value='http://return.url/foo?bar=buz&lorem=ipsum')
        self.assertQueryString(url, 'failure_url', value='http://failure.url/FOO?BAR=BUZ&LOREM=IPSUM')
        self.assertQueryString(url, 'muid', value='someone')
        self.assertQueryString(url, 'something', value='else')
        self.assertQueryString(url, 'BLUB', value=[b'b1', 'b2', u'u1', 'u2'])

    def test_get_subscribe_url(self):
        item = ItemDefinition(1, 'EUR20', 'http://example.net/t', 'title', sub_id='a0_-9Z', period=12345)
        url = self.lp.get_subscribe_url(
            item,
            product_key='some-product-key',
            dialog=False,
            return_url='http://return.url/foo?bar=buz&lorem=ipsum',
            failure_url='http://failure.url/FOO?BAR=BUZ&LOREM=IPSUM',
            muid='someone',
            something='else',
            period=12345,
            BLUB=[u'u2', b'b1', b'b2', u'u1'],
        )
        self.assertFalse(
            self.assertQueryString(url, 'expiry'),
            'expiry url param is "None". Should be omitted.'
        )
        self.assertQueryString(url, 'sub_id', value='a0_-9Z')
        self.assertQueryString(url, 'product_key', value='some-product-key')
        self.assertTrue(url.startswith('https://web.laterpay.net/subscribe?'))
        self.assertQueryString(url, 'return_url', value='http://return.url/foo?bar=buz&lorem=ipsum')
        self.assertQueryString(url, 'failure_url', value='http://failure.url/FOO?BAR=BUZ&LOREM=IPSUM')
        self.assertQueryString(url, 'muid', value='someone')
        self.assertQueryString(url, 'something', value='else')
        self.assertQueryString(url, 'period', value='12345')
        self.assertQueryString(url, 'BLUB', value=[b'b1', 'b2', u'u1', 'u2'])

    def test_get_login_dialog_url_with_use_dialog_api_false(self):
        url = self.lp.get_login_dialog_url('http://example.org')
        self.assertEqual(str(furl(url).path), '/account/dialog/login')

    def test_get_logout_dialog_url_with_use_dialog_api_false(self):
        url = self.lp.get_logout_dialog_url('http://example.org')
        self.assertEqual(str(furl(url).path), '/account/dialog/logout')

    def test_get_signup_dialog_url(self):
        url = self.lp.get_signup_dialog_url('http://example.org')
        self.assertEqual(str(furl(url).path), '/account/dialog/signup')

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

        self.assertEqual(call.request.headers['X-LP-APIVersion'], '2')

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
            'cp': '1',
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
