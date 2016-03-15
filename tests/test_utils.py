# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sys

import mock

from laterpay import utils
from laterpay import compat

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class UtilsTest(unittest.TestCase):

    def test_signed_query_correct_signature(self):
        params = {
            'parĄm1': 'valuĘ',
            'param2': ['value2', 'value3'],
            'ts': '1330088810',
        }
        url = 'https://endpoint.com/api'
        secret = 'secret'

        q = utils.signed_query(secret, params, url)

        self.assertEqual(
            q,
            'param2=value2&param2=value3&par%C4%84m1=valu%C4%98&'
            'ts=1330088810&hmac=01c928dcdbbf4ba467969ec9607bfdec0563524d93e06df7d8d3c80d'
        )

    @mock.patch('time.time')
    def test_signed_query_added_timestamp(self, time_time_mock):
        time_time_mock.return_value = 123

        params = {'foo': 'bar'}
        url = 'https://endpoint.com/api'
        secret = 'secret'

        qs = utils.signed_query(secret, params, url)
        qsd = compat.parse_qs(qs)

        self.assertEqual(qsd['ts'], ['123'])
        self.assertEqual(qsd['foo'], ['bar'])
