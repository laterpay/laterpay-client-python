#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys
import uuid

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

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
            ItemDefinition(1, 'EUR20', '', 'title')
        with self.assertRaises(InvalidItemDefinition):
            ItemDefinition(1, 'EUR20', '', 'title')
        with self.assertRaises(InvalidItemDefinition):
            ItemDefinition(1, 'EUR20', 'http://foo.invalid', 'title', expiry="illegal123")


class TestLaterPayClient(unittest.TestCase):

    def setUp(self):
        self.lp = LaterPayClient(
            1,
            'some-secret')

    def get_qs_dict(self, url):
        o = urlparse(url)
        d = parse_qs(o.query)
        o = urlparse(d['url'][0])
        d = parse_qs(o.query)
        return d

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


if __name__ == '__main__':
    unittest.main()
