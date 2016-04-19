# Changelog


## Unreleased
* The parameter `skip_add_to_invoice` in `LaterPayClient.get_add_url()` and 
  `LaterPayClient.get_buy_url()` is deprecated and will be removed in a future
  release.


## 4.2.0

* `laterpay.signing.sign_and_encode()` is deprecated and will be removed in a
  future release. Consider using `laterpay.utils.signed_query()` instead.
* `signing.sign_get_url()` is deprecated and will be removed in a future
  release.
* `LaterPayClient.get_access()` is deprecated and will be removed in a future
  release. Consider using `LaterPayClient.get_access_data()` instead.
* `LaterPayClient.get_identify_url()` is deprecated and will be removed in a future
  release.
* New utility functions: `laterpay.utils.signed_query()` and
  `laterpay.utils.signed_url()`
* New `LaterPayClient` methods:

    * `get_request_headers()`
    * `get_access_url()`
    * `get_access_params()`
    * `get_access_data()`

* Improved and newly added tests.
* Improved `laterpay.signing` docs.
* Replaced most of `compat` with proper `six` usage.


## 4.1.0

* Dialog API Wrapper is [deprecated](http://docs.laterpay.net/platform/dialogs/third_party_cookies/).
* `get_buy_url()`, `get_add_url()`, `get_login_dialog_url()`, `get_signup_dialog_url()`, and `get_logout_dialog_url()` have a new `use_dialog_api` parameter that sets if the URL returned uses the Dialog API Wrapper or not. Defaults to True during the Dialog API deprecation period.
* `ItemDefinition` no longer requires a `cp` argument.


## 4.0.0

* Exceptions raised by `urlopen` in `LaterPayClient._make_request()` are now logged with `ERROR` level using `Logger.exception()`.
* Added `timeout_seconds` (default value is 10) param to `LaterPayClient`. Backend API requests will time out now according to that value.
* Removed deprecated `laterpay.django` package.
* Removed deprecated `vat` and `purchasedatetime` params from `ItemDefinition.__init__()`. This is a backward incompatible change to `__init__(self, item_id, pricing, url, title, cp=None, expiry=None)` from `__init__(self, item_id, pricing, vat, url, title, purchasedatetime=None, cp=None, expiry=None)`.
* Removed deprecated `add_metered_access()` and `get_metered_access()` methods from `LaterPayClient`.


## 3.2.1

* Standardised the usage of the (internal) `product` API (it was usable via path or parameter, and we're deprecating the path usage)

## 3.2.0

* Deprecating the `vat` parameter in `ItemDefinition` because of new [EU law for calculating VAT](http://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32006L0112&from=DE)
* Deprecated `LaterPayClient.get_metered_access()` and `LaterPayClient.add_metered_access()` methods.
* Added `return_url` / `failure_url` parameters for dialogs: https://www.laterpay.net/developers/docs/dialog-api

## 3.1.0

* Support for Python 3.3 and 3.4 (https://github.com/laterpay/laterpay-client-python/pull/1)
* Improved documentation coverage
* Dropped distutils usage
* Fixed [an issue where omitted optional `ItemDefinition` data would be erroneously included in URLs as the string `"None"`](https://github.com/laterpay/laterpay-client-python/pull/19)
* Added deprecation warnings to several methods that never should have been considered part of the public API
* Deprecated the Django integration in favour of an explicit [`django-laterpay`](https://github.com/laterpay/django-laterpay) library.
* Added support for [expiring items](https://laterpay.net/developers/docs/dialog-api)

## 3.0.0 (Initial public release)

Existence
