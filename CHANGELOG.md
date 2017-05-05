# Changelog

## 5.3.0

* Added explicit support for the `muid` argument to `get_add_url()`,
  `get_buy_url()` and `get_subscribe_url()`.

* Added function to create manual ident URLs. A user can visit these URLs to
  regain access to previous purchased or bought content.

* Added [PyJWT](https://pyjwt.readthedocs.io/en/latest/) >= 1.4.2 to the
  installation requirements as it's required for the added manual ident URLs
  feature.

* Added support for `muid` when creating manual ident URLs.

* Added support to check for access based on `muid` instead of `lptoken`.

## 5.2.0

* Added constants outlining expiration and duration time bases for purchases

## 5.1.0

* Ignored HMAC character capitalization
  ([#93](https://github.com/laterpay/laterpay-client-python/issues/93))
* Added support for ``/dialog/subscribe`` and LaterPay's subscription system

## 5.0.0

* Removed the following long deprecated methods from the
  `laterpay.LaterPayClient`:

  * `get_access()`, use `get_access_data()` instead
  * `get_iframeapi_balance_url()`, us `get_controls_balance_url()` instead
  * `get_iframeapi_links_url()`, us `get_controls_links_url()` instead
  * `get_identify_url()` is not needed following our modern access control
    checks

* Removed the following deprecated arguments from `laterpay.LaterPayClient`
  methods:

  * `use_dialog_api` from `get_login_dialog_url()`
  * `use_dialog_api` from `get_signup_dialog_url()`
  * `use_dialog_api` from `get_logout_dialog_url()`

* Removed the following public methods from `laterpay.signing`:

  * `sign_and_encode()` in favor of `laterpay.utils.signed_query()`
  * `sign_get_url()` in favor of `laterpay.utils.signed_url()`

  Note that `sign_and_encode()` and `sign_get_url()` used to remove existing
  `'hmac'` parameters before signing query strings. This is different to
  `signed_query()` as that function also allows other names for the hmac query
  argument. Please remove the parameter yourself if need be.

* Removed the deprecated `cp` argument from `laterpay.ItemDefinition`

* Reliably ignore `hmac` and `gettoken` parameters when creating the signature
  message. In the past `signing.sign()` and `signing.verify()` stripped those
  keys when a `dict()` was passed from the passed function arguments but not
  for lists or tuples. Note that as a result the provided parameters are not
  touched anymore and calling either function will not have side-effects on
  the provided arguments.


## 4.6.0

* Fixed encoding issues when passing byte string parameters on Python 3
  ([#84](https://github.com/laterpay/laterpay-client-python/issues/84))


## 4.5.0

* Added support for Python requests >= 2.11
* Added current version number to HTTP request headers


## 4.4.1

* Enabled universal wheel builds


## 4.4.0

* `laterpay.utils.signed_query()` now passes a `dict` params instance to
  `laterpay.signing.sign()` which makes it compatible with `sign()` ignoring
  some params being ignored by `sign()` by looking them up with `in` operator.

* Added Python 3.5 support


## 4.3.0

* `LaterPayClient.get_add_url()` and `LaterPayClient.get_buy_url()` accept
  `**kwargs`.

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
* Added `return_url` / `failure_url` parameters for dialogs: http://docs.laterpay.net/platform/dialogs/

## 3.1.0

* Support for Python 3.3 and 3.4 (https://github.com/laterpay/laterpay-client-python/pull/1)
* Improved documentation coverage
* Dropped distutils usage
* Fixed [an issue where omitted optional `ItemDefinition` data would be erroneously included in URLs as the string `"None"`](https://github.com/laterpay/laterpay-client-python/pull/19)
* Added deprecation warnings to several methods that never should have been considered part of the public API
* Deprecated the Django integration in favour of an explicit [`django-laterpay`](https://github.com/laterpay/django-laterpay) library.
* Added support for [expiring items](hhttp://docs.laterpay.net/platform/dialogs/)

## 3.0.0 (Initial public release)

Existence
