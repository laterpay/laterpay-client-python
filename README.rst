laterpay-client-python
======================

.. image:: https://img.shields.io/pypi/v/laterpay-client.png
    :target: https://pypi.python.org/pypi/laterpay-client

.. image:: https://img.shields.io/travis/laterpay/laterpay-client-python/develop.png
    :target: https://travis-ci.org/laterpay/laterpay-client-python

.. image:: https://img.shields.io/coveralls/laterpay/laterpay-client-python/develop.png
    :target: https://coveralls.io/r/laterpay/laterpay-client-python


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

* Install ``twine`` with ``$ pipsi install twine``
* Ensure ``CHANGELOG.md`` is representative
* Determine next version number from the CHANGELOG (ensuring we follow `SemVer <http://semver.org/>`_)
* ``git flow release start $newver``
* Update the CHANGELOG with the new version
* Update the version in ``setup.py``
* ``git flow release finish $newver``
* ``git push --tags origin develop master``
* ``python setup.py sdist bdist_wheel``
* ``twine upload dist/laterpay*$newver*`` or optionally, for signed releases ``twine upload -s ...``
