ldif3 - generate and parse LDIF data (see `RFC 2849`_).

This is a fork of the ``ldif`` module from `python-ldap`_ with python3/unicode
support. See the first entry in CHANGES.rst for a more complete list of
differences.

Usage
-----

Parse LDIF from a file (or ``BytesIO``)::

    from ldif3 import LDIFParser
    from pprint import pprint

    parser = LDIFParser(open('data.ldif', 'rb'))
    for dn, entry in parser.parse():
        print('got entry record: %s' % dn)
        pprint(record)


Write LDIF to a file (or ``BytesIO``)::

    from ldif3 import LDIFWriter

    writer = LDIFWriter(open('data.ldif', 'wb'))
    writer.unparse('mail=alice@example.com', {
        'cn': ['Alice Alison'],
        'mail': ['alice@example.com'],
        'objectclass': ['top', 'person'],
    })

Unicode support
---------------

The stream object that is passed to parser or writer must be a byte
stream. It must use UTF-8 encoding as described in the spec.

The parsed objects (``dn`` and the keys and values of ``record``) on the
other hand are unicode strings.


.. _RFC 2849: https://tools.ietf.org/html/rfc2849
.. _python-ldap: http://www.python-ldap.org/
