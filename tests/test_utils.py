# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import unittest

import mock

from six.moves.urllib.parse import parse_qs

from laterpay import utils
from laterpay.compat import stringify


class UtilsTest(unittest.TestCase):

    def test_signed_query_correct_signature(self):
        params = {
            b'par\xc4\x84m1': u'valuĘ',
            'param2': ['value2', 'value3'],
            'ts': '1330088810',
        }
        url = 'https://endpoint.com/api'
        secret = 'secret'

        q = utils.signed_query(secret, params, url)

        qd = parse_qs(q)

        self.assertEqual(
            set(qd.keys()),
            set(['ts', 'parĄm1', 'param2', 'hmac']),
        )

        self.assertEqual(qd['ts'], [params['ts']])
        self.assertEqual(qd['param2'], params['param2'])
        self.assertEqual(
            qd['parĄm1'],
            [stringify(params[b'par\xc4\x84m1'])],
        )
        self.assertEqual(
            qd['hmac'],
            ['01c928dcdbbf4ba467969ec9607bfdec0563524d93e06df7d8d3c80d'],
        )

    @mock.patch('time.time')
    def test_signed_query_added_timestamp(self, time_time_mock):
        time_time_mock.return_value = 123

        params = {'foo': 'bar'}
        url = 'https://endpoint.com/api'
        secret = 'secret'

        qs = utils.signed_query(secret, params, url)
        qsd = parse_qs(qs)

        self.assertEqual(qsd['ts'], ['123'])
        self.assertEqual(qsd['foo'], ['bar'])

    @mock.patch('time.time')
    def test_signed_query_added_timestamp_params_not_dict(self, time_time_mock):
        time_time_mock.return_value = 123

        params = [('foo', 'bar')]
        url = 'https://endpoint.com/api'
        secret = 'secret'

        qs = utils.signed_query(secret, params, url)
        qsd = parse_qs(qs)

        self.assertEqual(qsd['ts'], ['123'])
        self.assertEqual(qsd['foo'], ['bar'])

    def test_signed_query_keep_duplicate_signature(self):
        params = {'foo': 'bar', 'ts': 123, 'hmac': 'blub'}
        url = 'https://endpoint.com/api'
        secret = 'secret'

        qs = utils.signed_query(secret, params, url)
        qsd = parse_qs(qs)

        self.assertEqual(qsd['ts'], ['123'])
        self.assertEqual(qsd['foo'], ['bar'])
        self.assertEqual(qsd['hmac'], ['blub', 'af319e7ec1b7f50e054ed934f22b05bd9ff58d7783da2549efba86c1'])

    def test_signed_url(self):
        params = {'foo': 'bar'}
        url = utils.signed_url(
            'secret',
            params,
            'http://example.net/here',
            add_timestamp=False,
            signature_param_name='sig',
        )
        self.assertEqual(
            url,
            'http://example.net/here?foo=bar'
            '&sig=83e26a62c0a3cf7405c7f2b4b75a46c4facc5c4dd013d57fa24936ce',
        )
