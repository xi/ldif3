3.2.1 (2016-12-27)
------------------

-   Ignore non-unicode characters in "dn" in non-strict mode. (Fixes `#4
    https://github.com/xi/ldif3/issues/6`_)


3.2.0 (2016-06-03)
------------------

-   Overhaule the unicode support to also support binary data (e.g. images)
    encoded in LDIF.

    You can now pass an encoding to the parser which will be used to decode
    values. If decoding failes, a bytestring will be returned.  If you pass an
    encoding of ``None``, the parser will not try to do any conversion and
    return bytes directly.

    This change should be completely backwards compatible, as the parser now
    gracefully handles a case where it crashed previously.

    (See `#4 <https://github.com/xi/ldif3/issues/4>`_)


3.1.1 (2015-09-20)
------------------

-   Allow empty values for attributes.


3.1.0 (2015-07-09)
------------------

This is mostly a reaction to `python-ldap 2.4.20
<https://mail.python.org/pipermail/python-ldap/2015q3/003557.html>`_.

-   Restore support for ``records_read`` as well as adding ``line_counter`` and
    ``byte_counter`` that were introduced in python-ldap 2.4.20.
-   Stricter order checking of ``dn:``.
-   Remove partial support for parsing change records. A more complete
    implementation based on improvements made in python-ldap may be included
    later.  But for now, I don't have the time.

    **Breaking change**: ``LDIFParser.parse()`` now yields ``dn, entry`` rather
    than ``dn, changetype, entry``.


3.0.2 (2015-06-22)
------------------

-   Include documentation source and changelog in source distribution.
    (Thanks to Michael Fladischer)
-   Add LICENSE file


3.0.1 (2015-05-22)
------------------

-   Use OrderedDict for entries.


3.0.0 (2015-05-22)
------------------

This is the first version of a fork of the ``ldif`` module from `python-ldap
<http://www.python-ldap.org/>`_.  For any changes before that, see the
documentation over there.  The last version before the fork was 2.4.15.

The changes introduced with this version are:

-   Dropped support for python < 2.7.
-   Added support for python 3, including unicode support.
-   All deprecated functions (``CreateLDIF``, ``ParseLDIF``) were removed.
-   ``LDIFCopy`` and ``LDIFRecordList`` were removed.
-   ``LDIFParser.handle()`` was removed.  Instead, ``LDIFParser.parse()``
    yields the records.
-   ``LDIFParser`` has now a ``strict`` option that defaults to ``True``
    for backwards-compatibility.  If set to ``False``, recoverable parse errors
    will produce log warnings rather than exceptions.
