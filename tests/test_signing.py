#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import hashlib
import unittest

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

    def test_create_message_wrong_method(self):
        params = {u'parĄm1': u'valuĘ'}
        url = u'https://endpoint.com/ąpi'

        with self.assertRaises(ValueError):
            signing.create_base_message(params, url, method='WRONG')

    def test_sign(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
        }
        url = u'https://endpoint.com/api'

        secret = u'secret'  # unicode is what we usually get from api/db..

        mac = signing.sign(secret, params, url)

        # sha224 hmac
        self.assertEqual(
            mac,
            '346f3d53ad762f3ed3fb7f2427dec2bbfaf0338bb7f91f0460aff15c',
        )

    def test_verify_str_signature(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
        }
        url = u'https://endpoint.com/api'

        secret = 'secret'

        verified = signing.verify(
            '346f3d53ad762f3ed3fb7f2427dec2bbfaf0338bb7f91f0460aff15c',
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
            'key3': ('value31', 'value32'),  # Do we want a list here?
        })

        params = [
            ['key1', 'value11'],
            ['key1', 'value12'],
            ('key2', ['value21', 'value22']),
            ('key3', ('value31', 'value32')),
        ]
        self.assertEqual(signing.normalise_param_structure(params), {
            'key1': ['value11', 'value12'],
            'key2': ['value21', 'value22'],
            'key3': ('value31', 'value32'),  # Do we want a list here?
        })


if __name__ == '__main__':
    unittest.main()
