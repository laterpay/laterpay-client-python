#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from laterpay import compat
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
        params = {'parĄm1': 'valuĘ'}
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
            'param2': ['value2', 'value3'],
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

    def test_sign_and_encode(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
            'ts': '1330088810',
        }
        url = u'https://endpoint.com/api'

        secret = u'secret'  # unicode is what we usually get from api/db..

        signed_and_encoded = signing.sign_and_encode(secret, params, url)

        self.assertEqual(
            signed_and_encoded,
            'param2=value2&param2=value3&par%C4%84m1=valu%C4%98&'
            'ts=1330088810&hmac=01c928dcdbbf4ba467969ec9607bfdec0563524d93e06df7d8d3c80d'
        )

    def test_verify(self):
        params = {
            u'parĄm1': u'valuĘ',
            'param2': ['value2', 'value3'],
        }
        url = u'https://endpoint.com/api'

        secret = u'secret'  # unicode is what we usually get from api/db..

        verified = signing.verify(
            '346f3d53ad762f3ed3fb7f2427dec2bbfaf0338bb7f91f0460aff15c',
            secret,
            params,
            url,
            'POST',
        )

        self.assertTrue(verified)

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

    def test_signing_with_item(self):
        secret = '401e9a684fcc49578c1f23176a730abc'
        base_url = 'http://local.laterpaytest.net:8005/dialog/mmss/buy'
        method = 'GET'

        # creating this data with ItemDefinition and copy.copy(item.data) doesn't work
        # since it has a purchase_date based on now(), so the signature isn't the same..
        data = {
            'article_id': [154],
            'cp': ['laternews'],
            'jsevents': [1],
            'pricing': ['EUR200'],
            'purchase_date': [1398861228815],
            'title': [u"VIDEO: Rwanda's genocide, 20 years on"],
            'tref': ['4ebbf443-a12e-4ce9-89e4-999ba93ba1dc'],
            'ts': ['1398861228'],
            'url': ['http://local.laterpaytest.net:8003/mmss/154'],
            'vat': ['EU19']
        }

        params = signing.sign_and_encode(secret, data, base_url, method)
        expected_string = 'article_id=154&cp=laternews&jsevents=1&pricing=EUR200&purchase_date=1398861228815&title=VIDEO%3A+Rwanda%27s+genocide%2C+20+years+on&tref=4ebbf443-a12e-4ce9-89e4-999ba93ba1dc&ts=1398861228&url=http%3A%2F%2Flocal.laterpaytest.net%3A8003%2Fmmss%2F154&vat=EU19&hmac=4d41f1adcb7c6bf6cf9c5eb15b179fdbec667d53f2749e2845c87315'  # noqa

        self.assertEqual(expected_string, params)

        # expected signature based on params above
        signature = '4d41f1adcb7c6bf6cf9c5eb15b179fdbec667d53f2749e2845c87315'

        self.assertTrue(signing.verify(signature, secret, data, base_url, method))

        # changing the price in the url
        false_string = 'article_id=154&cp=laternews&jsevents=1&pricing=EUR150&purchase_date=1398861228815&title=VIDEO%3A+Rwanda%27s+genocide%2C+20+years+on&tref=4ebbf443-a12e-4ce9-89e4-999ba93ba1dc&ts=1398861228&url=http%3A%2F%2Flocal.laterpaytest.net%3A8003%2Fmmss%2F154&vat=EU19&hmac=4d41f1adcb7c6bf6cf9c5eb15b179fdbec667d53f2749e2845c87315'  # noqa
        false_params = compat.parse_qs(false_string)

        self.assertFalse(signing.verify(signature, secret, false_params, base_url, method))

        # changing the base_url
        false_base_url = 'http://local.laterpaytest.net:8005/dialog/mmss/add'
        self.assertFalse(signing.verify(signature, secret, data, false_base_url, method))

        # changing http method
        false_method = 'POST'
        self.assertFalse(signing.verify(signature, secret, data, base_url, false_method))


if __name__ == '__main__':
    unittest.main()
