#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import hashlib
import unittest
import warnings

import furl

from laterpay import signing


class TestSigningHelper(unittest.TestCase):

    def test_create_message_unicode(self):
        params = {u'parĄm1': u'valuĘ'}
        url = u'https://endpoint.com/ąpi'

        msg = signing.create_base_message(params, url)

        self.assertEqual(
            msg,
            'POST&https%3A%2F%2Fendpoint.com%2F%C4%85pi&'
            'par%25C4%2584m1%3Dvalu%25C4%2598',
        )

    def test_create_message_bytestrings(self):
        params = {b'par\xc4\x84m1': b'valu\xc4\x98'}
        url = 'https://endpoint.com/ąpi'

        msg = signing.create_base_message(params, url)

        self.assertEqual(
            msg,
            'POST&https%3A%2F%2Fendpoint.com%2F%C4%85pi&'
            'par%25C4%2584m1%3Dvalu%25C4%2598',
        )

    def test_create_message_sorting_and_combining_params(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value3', 'value2'],
            u'param3': u'with a space'
        }
        url = 'https://endpoint.com/api'

        msg = signing.create_base_message(params, url)

        self.assertEqual(
            msg,
            'POST&'
            'https%3A%2F%2Fendpoint.com%2Fapi&'
            'par%25C4%2584m1%3Dvalu%25C4%2598'
            '%26param2%3Dvalue2'
            '%26param2%3Dvalue3'
            '%26param3%3Dwith%2520a%2520space',
        )

    def test_create_message_sorting_and_combining_params_omdict(self):
        params = furl.furl(
            '?par%C4%84m1=valu%C4%98'
            '&param2=value3'
            '&param2=value2'
            '&param3=with+a+space'
        ).query.params
        url = 'https://endpoint.com/api'

        msg = signing.create_base_message(params, url)

        self.assertEqual(
            msg,
            'POST&'
            'https%3A%2F%2Fendpoint.com%2Fapi&'
            'par%25C4%2584m1%3Dvalu%25C4%2598'
            '%26param2%3Dvalue2'
            '%26param2%3Dvalue3'
            '%26param3%3Dwith%2520a%2520space',
        )

    def test_create_message_wrong_method(self):
        params = {u'parĄm1': u'valuĘ'}
        url = u'https://endpoint.com/ąpi'

        with self.assertRaises(ValueError):
            signing.create_base_message(params, url, method='WRONG')

    def test_sign(self):
        signature = '5b341f4321476715ab1ae252794783c6dffa32dbdcc94512193ea3cf'
        params = {
            u'parĄm1': u'valuĘ',
            b'par\xc4\x84m1': ['value2', 'value3'],
            b'hmac': 'will-be-removed',
            u'gettoken': 'will-be-removed-too',
        }
        url = b'https://endpoint.com/api'
        secret = b'secret'

        # sha224 hmac
        self.assertEqual(signing.sign(secret, params, url), signature)

        # Test that `hmac` and `gettoken` are not being removed from the
        # original arguments passed to the function
        self.assertIn(b'hmac', params)
        self.assertIn(u'gettoken', params)

        del params[b'hmac']
        del params[u'gettoken']
        self.assertEqual(signing.sign(secret, params, url), signature)

    def test_sign_unicode_secret(self):
        signature = '635cef6498fc5f1a829275cc1b24a191d5267d6023034e3e0953e4c6'
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
            u'hmac': 'to-be-removed',
            b'gettoken': 'to-be-removed-too',
        }
        url = u'https://endpoint.com/api'
        secret = u'☃🐍'  # unicode is what we usually get from api/db..

        # sha224 hmac
        self.assertEqual(signing.sign(secret, params, url), signature)

        # Test that `hmac` and `gettoken` are not being removed from the
        # original arguments passed to the function
        self.assertIn(u'hmac', params)
        self.assertIn(b'gettoken', params)

        del params[u'hmac']
        del params[b'gettoken']
        self.assertEqual(signing.sign(secret, params, url), signature)

    def test_verify_byte_signature(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
        }
        url = u'https://endpoint.com/api'

        secret = 'secret'

        verified = signing.verify(
            b'346f3d53ad762f3ed3fb7f2427dec2bbfaf0338bb7f91f0460aff15c',
            secret,
            params,
            url,
            'POST',
        )
        self.assertTrue(verified)

    def test_verify_unicode_signature(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
        }
        url = u'https://endpoint.com/api'
        verified = signing.verify(
            u'346f3d53ad762f3ed3fb7f2427dec2bbfaf0338bb7f91f0460aff15c',
            u'secret',
            params,
            url,
            'POST',
        )
        self.assertTrue(verified)

    def test_verify_iterable_signature(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
        }
        url = u'https://endpoint.com/api'

        secret = 'secret'

        verified = signing.verify(
            ['346f3d53ad762f3ed3fb7f2427dec2bbfaf0338bb7f91f0460aff15c', 'blub'],
            secret,
            params,
            url,
            'POST',
        )
        self.assertTrue(verified)

        verified = signing.verify(
            ('346f3d53ad762f3ed3fb7f2427dec2bbfaf0338bb7f91f0460aff15c', 'blub'),
            secret,
            params,
            url,
            'POST',
        )
        self.assertTrue(verified)

    def test_verify_invalid_unicode_signature(self):
        params = {}
        url = 'https://endpoint.com/api'
        secret = 'secret'

        verified = signing.verify(
            u'Ɛ' * len(hashlib.sha224(b'').hexdigest()),
            secret,
            params,
            url,
            'POST',
        )
        self.assertFalse(verified)

    def test_url_verification(self):
        secret = '401e9a684fcc49578c1f23176a730abc'
        url = 'http://example.com'
        method = 'GET'

        params = {
            'ts': '1330088810',
            'cp': 'laternews',
            'method': method,
            'hmac': 'f6e5b115ea9056e322c87540f12a4e6d52d717e233beff3556cf9601',
        }

        true_params = params.copy()
        self.assertTrue(signing.verify(true_params['hmac'], secret, true_params, url, method))

        false_params = params.copy()
        false_params['hmac'] = 'e9a684fcc23176a730abc49578c1f13b'
        self.assertFalse(signing.verify(false_params['hmac'], secret, false_params, url, method))

        false_params = params.copy()
        del false_params['cp']
        self.assertFalse(signing.verify(false_params['hmac'], secret, false_params, url, method))

        false_params = params.copy()
        false_params['ts'] = '1234567890'
        self.assertFalse(signing.verify(false_params['hmac'], secret, false_params, url, method))

    def test_normalise_param_structure(self):
        params = {
            'key1': 'value1',
            'key2': ['value21', 'value22'],
            'key3': ('value31', 'value32'),
        }
        self.assertEqual(signing.normalise_param_structure(params), {
            'key1': ['value1'],
            'key2': ['value21', 'value22'],
            'key3': ['value31', 'value32'],  # Converted from tuple to list
        })

        params = [
            [b'key1', 'value11'],
            [u'key1', 'value12'],
            ('key2', ['value21', 'value22']),
            ('key3', ('value31', 'value32')),
        ]
        self.assertEqual(signing.normalise_param_structure(params), {
            'key1': ['value11', 'value12'],
            'key2': ['value21', 'value22'],
            'key3': ['value31', 'value32'],  # Converted from tuple to list
        })

        with self.assertRaises(TypeError):
            signing.normalise_param_structure('not a dict, list or tuple')

    def test_sort_params(self):
        params = {
            'key1': 'value1',
            'key2': ['value22', 'value21'],
            'key3': ('value32', 'value31'),
        }
        self.assertEqual(signing._sort_params(params), [
            ('key1', 'value1'),
            ('key2', 'value21'),
            ('key2', 'value22'),
            ('key3', 'value31'),
            ('key3', 'value32'),
        ])

    def test_sort_params_public_deprecation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            signing.sort_params({})
        self.assertEqual(
            w[0].message.args[0],
            'laterpay.signing.sort_params is deprecated and will be removed in future '
            'versions. Use laterpay.signing.normalise_param_structure instead.'
        )


if __name__ == '__main__':
    unittest.main()
