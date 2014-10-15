# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import unittest

from django.conf import settings

# Configure settings before attempting to import modules depending on them.
settings.configure()

from laterpay.django.middleware import LPTokenMiddleware


class RequestMock:

    def __init__(self, path):
        self.path = path


class MiddlewareTest(unittest.TestCase):

    def test_exempt_paths(self):
        paths = ('/one', '/two')
        LPTokenMiddleware.add_exempt_paths(*paths)

        for path in paths:
            request = RequestMock(path)
            m = LPTokenMiddleware()
            self.assertEqual(m.process_request(request), None)
