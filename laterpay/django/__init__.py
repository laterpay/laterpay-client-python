from django.conf import settings
from laterpay import LaterPayClient

import warnings

warnings.warn("laterpay.django deprecated in favour of the distinct `django-laterpay` library (`djlaterpay`) and will be removed in version 4 - please see https://github.com/laterpay/django-laterpay", DeprecationWarning)


def get_laterpay_client(lptoken):
    api_root = getattr(settings, 'LP_API_ROOT', None)
    web_root = getattr(settings, 'LP_WEB_ROOT', None)

    return LaterPayClient(settings.LP_CONTENT_PROVIDER_KEY,
                          settings.LP_SECRET,
                          api_root=api_root,
                          web_root=web_root,
                          lptoken=lptoken)
