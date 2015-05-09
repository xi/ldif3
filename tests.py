from __future__ import unicode_literals

import unittest

from io import StringIO

import ldif3


BYTES = """version: 1
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

BYTES_OUT = """dn: cn=Alice Alison,mail=alicealison@example.com
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

LINES = [
    "version: 1",
    "dn: cn=Alice Alison,mail=alicealison@example.com",
    "objectclass: top",
    "objectclass: person",
    "objectclass: organizationalPerson",
    "cn: Alison Alison",
    "mail: alicealison@example.com",
    "modifytimestamp: 4a463e9a",
    "",
    "dn: mail=foobar@example.org",
    "objectclass: top",
    "objectclass:  person",
    "mail: foobar@example.org",
    "modifytimestamp: 4a463e9a",
]

BLOCKS = [[
    "version: 1",
    "dn: cn=Alice Alison,mail=alicealison@example.com",
    "objectclass: top",
    "objectclass: person",
    "objectclass: organizationalPerson",
    "cn: Alison Alison",
    "mail: alicealison@example.com",
    "modifytimestamp: 4a463e9a",
], [
    "dn: mail=foobar@example.org",
    "objectclass: top",
    "objectclass:  person",
    "mail: foobar@example.org",
    "modifytimestamp: 4a463e9a",
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

URL = 'https://tools.ietf.org/rfc/rfc2849.txt'
URL_CONTENT = 'The LDAP Data Interchange Format (LDIF)'


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
        pass


class TestLDIFParser(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO(BYTES)
        self.p = ldif3.LDIFParser(self.stream)

    def test_strip_line_sep(self):
        self.assertEqual(self.p._strip_line_sep('asd \n'), 'asd ')
        self.assertEqual(self.p._strip_line_sep('asd\t\n'), 'asd\t')
        self.assertEqual(self.p._strip_line_sep('asd\r\n'), 'asd')
        self.assertEqual(self.p._strip_line_sep('asd\r\t\n'), 'asd\r\t')
        self.assertEqual(self.p._strip_line_sep('asd\n\r'), 'asd\n\r')
        self.assertEqual(self.p._strip_line_sep('asd'), 'asd')
        self.assertEqual(self.p._strip_line_sep('  asd  '), '  asd  ')

    def test_iter_unfolded_lines(self):
        self.assertEqual(list(self.p._iter_unfolded_lines()), LINES)

    def test_iter_blocks(self):
        self.assertEqual(list(self.p._iter_blocks()), BLOCKS)

    def test_check_dn_not_none(self):
        with self.assertRaises(ValueError):
            self.p._check_dn('some dn', 'mail=alicealison@example.com')

    def test_check_dn_invalid(self):
        with self.assertRaises(ValueError):
            self.p._check_dn(None, 'invalid')

    def test_check_dn_happy(self):
        self.p._check_dn(None, 'mail=alicealison@example.com')

    def test_check_changetype_dn_none(self):
        with self.assertRaises(ValueError):
            self.p._check_changetype(None, None, 'add')

    def test_check_changetype_not_none(self):
        with self.assertRaises(ValueError):
            self.p._check_changetype('some dn', 'some changetype', 'add')

    def test_check_changetype_invalid(self):
        with self.assertRaises(ValueError):
            self.p._check_changetype('some dn', None, 'invalid')

    def test_check_changetype_happy(self):
        self.p._check_changetype('some dn', None, 'add')

    def test_parse_attr_base64(self):
        attr_type, attr_value = self.p._parse_attr('foo:: YQpiCmM=\n')
        self.assertEqual(attr_type, 'foo')
        self.assertEqual(attr_value, 'a\nb\nc')

    def test_parse_attr_url(self):
        self.p._process_url_schemes = ['https']
        attr_type, attr_value = self.p._parse_attr('foo:< %s\n' % URL)
        self.assertIn(URL_CONTENT, attr_value)

    def test_parse_attr_url_all_ignored(self):
        attr_type, attr_value = self.p._parse_attr('foo:< %s\n' % URL)
        self.assertIsNone(attr_value)

    def test_parse_attr_url_this_ignored(self):
        self.p._process_url_schemes = ['file']
        attr_type, attr_value = self.p._parse_attr('foo:< %s\n' % URL)
        self.assertIsNone(attr_value)

    def test_parse(self):
        items = list(self.p.parse())
        for i, item in enumerate(items):
            dn, changetype, record = item

            self.assertEqual(dn, DNS[i])
            self.assertEqual(changetype, CHANGETYPES[i])
            self.assertEqual(record, RECORDS[i])


class TestLDIFWriter(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO()
        self.w = ldif3.LDIFWriter(self.stream)

    def test_fold_line_10_n(self):
        self.w._cols = 10
        self.w._line_sep = '\n'
        self.w._fold_line('abcdefghijklmnopqrstuvwxyz')
        folded = 'abcdefghij\n klmnopqrs\n tuvwxyz\n'
        self.assertEqual(self.stream.getvalue(), folded)

    def test_fold_line_12_underscore(self):
        self.w._cols = 12
        self.w._line_sep = '__'
        self.w._fold_line('abcdefghijklmnopqrstuvwxyz')
        folded = 'abcdefghijkl__ mnopqrstuvw__ xyz__'
        self.assertEqual(self.stream.getvalue(), folded)

    def test_fold_line_oneline(self):
        self.w._cols = 100
        self.w._line_sep = '\n'
        self.w._fold_line('abcdefghijklmnopqrstuvwxyz')
        folded = 'abcdefghijklmnopqrstuvwxyz\n'
        self.assertEqual(self.stream.getvalue(), folded)

    def test_needs_base64_encoding_forced(self):
        self.w._base64_attrs = ['attr_type']
        result = self.w._needs_base64_encoding('attr_type', 'attr_value')
        self.assertTrue(result)

    def test_needs_base64_encoding_not_save(self):
        result = self.w._needs_base64_encoding('attr_type', '\r')
        self.assertTrue(result)

    def test_needs_base64_encoding_save(self):
        result = self.w._needs_base64_encoding('attr_type', 'abcABC123_+')
        self.assertFalse(result)

    def test_unparse_attr_base64(self):
        self.w._unparse_attr('foo', 'a\nb\nc')
        value = self.stream.getvalue()
        self.assertEqual(value, 'foo:: YQpiCmM=\n')

    def test_unparse_entry_record(self):
        self.w._unparse_entry_record(RECORDS[0])
        value = self.stream.getvalue()
        self.assertEqual(value, (
            'cn: Alison Alison\n'
            'mail: alicealison@example.com\n'
            'modifytimestamp: 4a463e9a\n'
            'objectclass: top\n'
            'objectclass: person\n'
            'objectclass: organizationalPerson\n'))

    def test_unparse_changetype_add(self):
        self.w._unparse_changetype(2)
        value = self.stream.getvalue()
        self.assertEqual(value, 'changetype: add\n')

    def test_unparse_changetype_modify(self):
        self.w._unparse_changetype(3)
        value = self.stream.getvalue()
        self.assertEqual(value, 'changetype: modify\n')

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
