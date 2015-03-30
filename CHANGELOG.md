# Changelog

## UNRELEASED

* Deprecating the `vat` parameter in `ItemDefinition` because of new [EU law for calculating VAT](http://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32006L0112&from=DE)
* Deprecated `LaterPayClient.get_metered_access()` and `LaterPayClient.add_metered_access()` methods.

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
