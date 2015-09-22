from __future__ import unicode_literals

import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from io import BytesIO

import ldif3


BYTES = b"""version: 1
dn: cn=Alice Alison,
 mail=alicealison@example.com
objectclass: top
objectclass: person
objectclass: organizationalPerson
cn: Alison Alison
mail: alicealison@example.com
modifytimestamp: 4a463e9a

# another person
dn: mail=foobar@example.org
objectclass: top
objectclass:  person
mail: foobar@example.org
modifytimestamp: 4a463e9a
"""

BYTES_OUT = b"""dn: cn=Alice Alison,mail=alicealison@example.com
cn: Alison Alison
mail: alicealison@example.com
modifytimestamp: 4a463e9a
objectclass: top
objectclass: person
objectclass: organizationalPerson

dn: mail=foobar@example.org
mail: foobar@example.org
modifytimestamp: 4a463e9a
objectclass: top
objectclass: person

"""

BYTES_EMPTY_ATTR_VALUE = b"""dn: uid=foo123,dc=ws1,dc=webhosting,o=eim
uid: foo123
domainname: foo.bar
homeDirectory: /foo/bar.local
aliases:
aliases: foo.bar
"""

LINES = [
    b'version: 1',
    b'dn: cn=Alice Alison,mail=alicealison@example.com',
    b'objectclass: top',
    b'objectclass: person',
    b'objectclass: organizationalPerson',
    b'cn: Alison Alison',
    b'mail: alicealison@example.com',
    b'modifytimestamp: 4a463e9a',
    b'',
    b'dn: mail=foobar@example.org',
    b'objectclass: top',
    b'objectclass:  person',
    b'mail: foobar@example.org',
    b'modifytimestamp: 4a463e9a',
]

BLOCKS = [[
    b'version: 1',
    b'dn: cn=Alice Alison,mail=alicealison@example.com',
    b'objectclass: top',
    b'objectclass: person',
    b'objectclass: organizationalPerson',
    b'cn: Alison Alison',
    b'mail: alicealison@example.com',
    b'modifytimestamp: 4a463e9a',
], [
    b'dn: mail=foobar@example.org',
    b'objectclass: top',
    b'objectclass:  person',
    b'mail: foobar@example.org',
    b'modifytimestamp: 4a463e9a',
]]

DNS = [
    'cn=Alice Alison,mail=alicealison@example.com',
    'mail=foobar@example.org'
]

CHANGETYPES = [None, None]

RECORDS = [{
    'cn': ['Alison Alison'],
    'mail': ['alicealison@example.com'],
    'modifytimestamp': ['4a463e9a'],
    'objectclass': ['top', 'person', 'organizationalPerson'],
}, {
    'mail': ['foobar@example.org'],
    'modifytimestamp': ['4a463e9a'],
    'objectclass': ['top', 'person'],
}]

URL = b'https://tools.ietf.org/rfc/rfc2849.txt'
URL_CONTENT = 'The LDAP Data Interchange Format (LDIF)'


class TestUnsafeString(unittest.TestCase):
    unsafe_chars = ['\0', '\n', '\r']
    unsafe_chars_init = unsafe_chars + [' ', ':', '<']

    def _test_all(self, unsafes, fn):
        for i in range(128):  # TODO: test range(255)
            try:
                match = ldif3.UNSAFE_STRING_RE.search(fn(i))
                if i <= 127 and chr(i) not in unsafes:
                    self.assertIsNone(match)
                else:
                    self.assertIsNotNone(match)
            except AssertionError:
                print(i)
                raise

    def test_unsafe_chars(self):
        self._test_all(self.unsafe_chars, lambda i: 'a%s' % chr(i))

    def test_unsafe_chars_init(self):
        self._test_all(self.unsafe_chars_init, lambda i: '%s' % chr(i))

    def test_example(self):
        s = 'cn=Alice, Alison,mail=Alice.Alison@example.com'
        self.assertIsNone(ldif3.UNSAFE_STRING_RE.search(s))

    def test_trailing_newline(self):
        self.assertIsNotNone(ldif3.UNSAFE_STRING_RE.search('asd\n'))


class TestLower(unittest.TestCase):
    def test_happy(self):
        self.assertEqual(ldif3.lower(['ASD', 'HuHu']), ['asd', 'huhu'])

    def test_falsy(self):
        self.assertEqual(ldif3.lower(None), [])

    def test_dict(self):
        self.assertEqual(ldif3.lower({'Foo': 'bar'}), ['foo'])

    def test_set(self):
        self.assertEqual(ldif3.lower(set(['FOo'])), ['foo'])


class TestIsDn(unittest.TestCase):
    def test_happy(self):
        pass  # TODO


class TestLDIFParser(unittest.TestCase):
    def setUp(self):
        self.stream = BytesIO(BYTES)
        self.p = ldif3.LDIFParser(self.stream)

    def test_strip_line_sep(self):
        self.assertEqual(self.p._strip_line_sep(b'asd \n'), b'asd ')
        self.assertEqual(self.p._strip_line_sep(b'asd\t\n'), b'asd\t')
        self.assertEqual(self.p._strip_line_sep(b'asd\r\n'), b'asd')
        self.assertEqual(self.p._strip_line_sep(b'asd\r\t\n'), b'asd\r\t')
        self.assertEqual(self.p._strip_line_sep(b'asd\n\r'), b'asd\n\r')
        self.assertEqual(self.p._strip_line_sep(b'asd'), b'asd')
        self.assertEqual(self.p._strip_line_sep(b'  asd  '), b'  asd  ')

    def test_iter_unfolded_lines(self):
        self.assertEqual(list(self.p._iter_unfolded_lines()), LINES)

    def test_iter_blocks(self):
        self.assertEqual(list(self.p._iter_blocks()), BLOCKS)

    def _test_error(self, fn):
        self.p._strict = True
        with self.assertRaises(ValueError):
            fn()

        with mock.patch('ldif3.log.warning') as warning:
            self.p._strict = False
            fn()
            assert warning.called

    def test_check_dn_not_none(self):
        self._test_error(lambda:
            self.p._check_dn('some dn', 'mail=alicealison@example.com'))

    def test_check_dn_invalid(self):
        self._test_error(lambda:
            self.p._check_dn(None, 'invalid'))

    def test_check_dn_happy(self):
        self.p._check_dn(None, 'mail=alicealison@example.com')

    def test_check_changetype_dn_none(self):
        self._test_error(lambda:
            self.p._check_changetype(None, None, 'add'))

    def test_check_changetype_not_none(self):
        self._test_error(lambda:
            self.p._check_changetype('some dn', 'some changetype', 'add'))

    def test_check_changetype_invalid(self):
        self._test_error(lambda:
            self.p._check_changetype('some dn', None, 'invalid'))

    def test_check_changetype_happy(self):
        self.p._check_changetype('some dn', None, 'add')

    def test_parse_attr_base64(self):
        attr_type, attr_value = self.p._parse_attr(b'foo:: YQpiCmM=\n')
        self.assertEqual(attr_type, 'foo')
        self.assertEqual(attr_value, 'a\nb\nc')

    def test_parse_attr_url(self):
        self.p._process_url_schemes = [b'https']
        attr_type, attr_value = self.p._parse_attr(b'foo:< ' + URL + b'\n')
        self.assertIn(URL_CONTENT, attr_value)

    def test_parse_attr_url_all_ignored(self):
        attr_type, attr_value = self.p._parse_attr(b'foo:< ' + URL + b'\n')
        self.assertEqual(attr_value, '')

    def test_parse_attr_url_this_ignored(self):
        self.p._process_url_schemes = [b'file']
        attr_type, attr_value = self.p._parse_attr(b'foo:< ' + URL + b'\n')
        self.assertEqual(attr_value, '')

    def test_parse(self):
        items = list(self.p.parse())
        for i, item in enumerate(items):
            dn, record = item

            self.assertEqual(dn, DNS[i])
            self.assertEqual(record, RECORDS[i])


class TestLDIFParserEmptyAttrValue(unittest.TestCase):
    def setUp(self):
        self.stream = BytesIO(BYTES_EMPTY_ATTR_VALUE)
        self.p = ldif3.LDIFParser(self.stream)

    def test_parse(self):
        try:
            list(self.p.parse())
        except UnboundLocalError:
            self.fail('UnboundLocalError raised')


class TestLDIFWriter(unittest.TestCase):
    def setUp(self):
        self.stream = BytesIO()
        self.w = ldif3.LDIFWriter(self.stream)

    def test_fold_line_10_n(self):
        self.w._cols = 10
        self.w._line_sep = b'\n'
        self.w._fold_line(b'abcdefghijklmnopqrstuvwxyz')
        folded = b'abcdefghij\n klmnopqrs\n tuvwxyz\n'
        self.assertEqual(self.stream.getvalue(), folded)

    def test_fold_line_12_underscore(self):
        self.w._cols = 12
        self.w._line_sep = b'__'
        self.w._fold_line(b'abcdefghijklmnopqrstuvwxyz')
        folded = b'abcdefghijkl__ mnopqrstuvw__ xyz__'
        self.assertEqual(self.stream.getvalue(), folded)

    def test_fold_line_oneline(self):
        self.w._cols = 100
        self.w._line_sep = b'\n'
        self.w._fold_line(b'abcdefghijklmnopqrstuvwxyz')
        folded = b'abcdefghijklmnopqrstuvwxyz\n'
        self.assertEqual(self.stream.getvalue(), folded)

    def test_needs_base64_encoding_forced(self):
        self.w._base64_attrs = ['attr_type']
        result = self.w._needs_base64_encoding('attr_type', 'attr_value')
        self.assertTrue(result)

    def test_needs_base64_encoding_not_safe(self):
        result = self.w._needs_base64_encoding('attr_type', '\r')
        self.assertTrue(result)

    def test_needs_base64_encoding_safe(self):
        result = self.w._needs_base64_encoding('attr_type', 'abcABC123_+')
        self.assertFalse(result)

    def test_unparse_attr_base64(self):
        self.w._unparse_attr('foo', 'a\nb\nc')
        value = self.stream.getvalue()
        self.assertEqual(value, b'foo:: YQpiCmM=\n')

    def test_unparse_entry_record(self):
        self.w._unparse_entry_record(RECORDS[0])
        value = self.stream.getvalue()
        self.assertEqual(value, (
            b'cn: Alison Alison\n'
            b'mail: alicealison@example.com\n'
            b'modifytimestamp: 4a463e9a\n'
            b'objectclass: top\n'
            b'objectclass: person\n'
            b'objectclass: organizationalPerson\n'))

    def test_unparse_changetype_add(self):
        self.w._unparse_changetype(2)
        value = self.stream.getvalue()
        self.assertEqual(value, b'changetype: add\n')

    def test_unparse_changetype_modify(self):
        self.w._unparse_changetype(3)
        value = self.stream.getvalue()
        self.assertEqual(value, b'changetype: modify\n')

    def test_unparse_changetype_other(self):
        with self.assertRaises(ValueError):
            self.w._unparse_changetype(4)
        with self.assertRaises(ValueError):
            self.w._unparse_changetype(1)

    def test_unparse(self):
        for i, record in enumerate(RECORDS):
            self.w.unparse(DNS[i], record)
        value = self.stream.getvalue()
        self.assertEqual(value, BYTES_OUT)

    def test_unparse_fail(self):
        with self.assertRaises(ValueError):
            self.w.unparse(DNS[0], 'foo')
