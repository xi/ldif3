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

The stream object that is passed to parser or writer must be an ascii byte
stream.

The spec allows to include arbitrary data in base64 encoding or via URL. There
is no way of knowing the encoding of this data. To handle this, there are two
modes:

The default mode will try to interpret everything as UTF-8 and leave only the
strings that failed to encode/decode as bytes. The strict mode will not try to
do any conversio and return bytes directly.


.. _RFC 2849: https://tools.ietf.org/html/rfc2849
.. _python-ldap: http://www.python-ldap.org/
