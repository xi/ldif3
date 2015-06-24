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
