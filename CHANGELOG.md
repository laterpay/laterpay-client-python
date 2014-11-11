# Changelog

## UNRELEASED

* Support for Python 3.3 and 3.4 (https://github.com/laterpay/laterpay-client-python/pull/1)
* Improved documentation coverage
* Dropped distutils usage
* Fixed [an issue where omitted optional `ItemDefinition` data would be erroneously included in URLs as the string `"None"`](https://github.com/laterpay/laterpay-client-python/pull/19)
* Added deprecation warnings to several methods that never should have been considered part of the public API
* Deprecated the Django integration in favour of an explicit [`django-laterpay`](https://github.com/laterpay/django-laterpay) library.

## 3.0.0 (Initial public release)

Existence
