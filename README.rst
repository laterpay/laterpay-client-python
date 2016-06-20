laterpay-client-python
======================

.. image:: https://badge.fury.io/py/laterpay-client.png
    :target: http://badge.fury.io/py/laterpay-client

.. image:: https://travis-ci.org/laterpay/laterpay-client-python.png?branch=develop
    :target: https://travis-ci.org/laterpay/laterpay-client-python

.. image:: https://coveralls.io/repos/laterpay/laterpay-client-python/badge.png?branch=develop
    :target: https://coveralls.io/r/laterpay/laterpay-client-python

.. image:: https://pypip.in/d/laterpay-client/badge.png
    :target: https://crate.io/packages/laterpay-client?version=latest


`LaterPay <http://www.laterpay.net/>`__ Python client.

If you're using `Django <https://www.djangoproject.com/>`__ then you probably want to look at `django-laterpay <https://github.com/laterpay/django-laterpay>`__

Installation
------------

::

    $ pip install laterpay-client

Usage
-----

See http://docs.laterpay.net/

Development
-----------

See https://github.com/laterpay/laterpay-client-python

`Tested by Travis <https://travis-ci.org/laterpay/laterpay-client-python>`__

Release Checklist
-----------------

* Install `twine` with `$ pipsi install twine`
* Ensure CHANGELOG is representative
* Determine next version number from the CHANGELOG (ensuring we follow `SemVer <http://semver.org/>`_)
* `git flow release start $newver`
* Update the CHANGELOG with the new version
* Update the version in `setup.py`
* `git flow release finish $newver`
* `git push --tags origin develop master`
* `python setup.py sdist bdist_wheel`
* `twine upload dist/laterpay*$newver*` or optionally, for signed releases `twine upload -s ...`
