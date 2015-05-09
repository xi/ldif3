"""ldif3 - generate and parse LDIF data (see RFC 2849)."""

from __future__ import unicode_literals

__version__ = '2.4.15'

__all__ = [
    # constants
    'LDIF_PATTERN',
    # classes
    'LDIFWriter',
    'LDIFParser',
]

import base64
import re

try:
    from urlparse import urlparse
    from urllib import urlopen
except ImportError:
    from urllib.parse import urlparse
    from urllib.request import urlopen


ATTRTYPE_PATTERN = r'[\w;.-]+(;[\w_-]+)*'
ATTRVALUE_PATTERN = r'(([^,]|\\,)+|".*?")'
ATTR_PATTERN = ATTRTYPE_PATTERN + r'[ ]*=[ ]*' + ATTRVALUE_PATTERN
RDN_PATTERN = ATTR_PATTERN + r'([ ]*\+[ ]*' + ATTR_PATTERN + r')*[ ]*'
DN_PATTERN = RDN_PATTERN + r'([ ]*,[ ]*' + RDN_PATTERN + r')*[ ]*'
DN_REGEX = re.compile('^%s$' % DN_PATTERN)

LDIF_PATTERN = ('^((dn(:|::) %(DN_PATTERN)s)|(%(ATTRTYPE_PATTERN)'
    's(:|::) .*)$)+' % vars())

MOD_OPS = ['add', 'delete', 'replace']
CHANGE_TYPES = ['add', 'delete', 'modify', 'modrdn']


def is_dn(s):
    """Return True if s is a LDAP DN."""
    if s == '':
        return True
    rm = DN_REGEX.match(s)
    return rm is not None and rm.group(0) == s


SAFE_STRING_PATTERN = '(^(\000|\n|\r| |:|<)|[\000\n\r\200-\377]+|[ ]+$)'
SAFE_STRING_RE = re.compile(SAFE_STRING_PATTERN)


def lower(l):
    """Return a list with the lowercased items of l."""
    return [i.lower() for i in l or []]


class LDIFWriter(object):
    """Write LDIF entry or change records to file object.

    Copy LDIF input to a file output object containing all data retrieved
    via URLs.
    """

    def __init__(self, output_file, base64_attrs=None, cols=76, line_sep='\n'):
        """
        output_file
            file object for output
        base64_attrs
            list of attribute types to be base64-encoded in any case
        cols
            Specifies how many columns a line may have before it's
            folded into many lines.
        line_sep
            String used as line separator
        """
        self._output_file = output_file
        self._base64_attrs = lower(base64_attrs)
        self._cols = cols
        self._line_sep = line_sep
        self.records_written = 0

    def _fold_line(self, line):
        """Write string line as one or more folded lines."""
        if len(line) <= self._cols:
            self._output_file.write(line)
            self._output_file.write(self._line_sep)
        else:
            pos = self._cols
            self._output_file.write(line[0:self._cols])
            self._output_file.write(self._line_sep)
            while pos < len(line):
                self._output_file.write(' ')
                end = min(len(line), pos + self._cols - 1)
                self._output_file.write(line[pos:end])
                self._output_file.write(self._line_sep)
                pos = end

    def _needs_base64_encoding(self, attr_type, attr_value):
        """Return True if attr_value has to be base-64 encoded.

        This is the case because of special chars or because attr_type is in
        self._base64_attrs
        """
        return attr_type.lower() in self._base64_attrs or \
                SAFE_STRING_RE.search(attr_value) is not None

    def _unparse_attr(self, attr_type, attr_value):
        """Write a single attribute type/value pair."""
        if self._needs_base64_encoding(attr_type, attr_value):
            encoded = base64.encodestring(attr_value).replace('\n', '')
            self._fold_line(':: '.join([attr_type, encoded]))
        else:
            self._fold_line(': '.join([attr_type, attr_value]))

    def _unparse_entry_record(self, entry):
        """
        entry
            dictionary holding an entry
        """
        for attr_type in sorted(entry.keys()):
            for attr_value in entry[attr_type]:
                self._unparse_attr(attr_type, attr_value)

    def _unparse_changetype(self, mod_len):
        """Detect and write the changetype."""
        if mod_len == 2:
            changetype = 'add'
        elif mod_len == 3:
            changetype = 'modify'
        else:
            raise ValueError("modlist item of wrong length")

        self._unparse_attr('changetype', changetype)

    def _unparse_change_record(self, modlist):
        """
        modlist
            list of additions (2-tuple) or modifications (3-tuple)
        """
        mod_len = len(modlist[0])
        self._unparse_changetype(mod_len)

        for mod in modlist:
            if len(mod) != mod_len:
                raise ValueError("Subsequent modlist item of wrong length")

            if mod_len == 2:
                mod_type, mod_vals = mod
            elif mod_len == 3:
                mod_op, mod_type, mod_vals = mod
                self._unparse_attr(MOD_OPS[mod_op], mod_type)

            for mod_val in mod_vals:
                self._unparse_attr(mod_type, mod_val)

            if mod_len == 3:
                self._output_file.write('-' + self._line_sep)

    def unparse(self, dn, record):
        """
        dn
            string-representation of distinguished name
        record
            Either a dictionary holding the LDAP entry {attrtype:record}
            or a list with a modify list like for LDAPObject.modify().
        """
        self._unparse_attr('dn', dn)
        if isinstance(record, dict):
            self._unparse_entry_record(record)
        elif isinstance(record, list):
            self._unparse_change_record(record)
        else:
            raise ValueError("Argument record must be dictionary or list")
        self._output_file.write(self._line_sep)
        self.records_written += 1


class LDIFParser(object):
    """Base class for a LDIF parser."""

    def _strip_line_sep(self, s):
        """Strip trailing line separators from s, but no other whitespaces."""
        if s[-2:] == '\r\n':
            return s[:-2]
        elif s[-1:] == '\n':
            return s[:-1]
        else:
            return s

    def __init__(
            self,
            input_file,
            ignored_attr_types=None,
            process_url_schemes=None,
            line_sep='\n'):
        """
        Parameters:
        input_file
            File-object to read the LDIF input from
        ignored_attr_types
            Attributes with these attribute type names will be ignored.
        process_url_schemes
            List containing strings with URLs schemes to process with urllib.
            An empty list turns off all URL processing and the attribute
            is ignored completely.
        line_sep
            String used as line separator
        """
        self._input_file = input_file
        self._process_url_schemes = lower(process_url_schemes)
        self._ignored_attr_types = lower(ignored_attr_types)
        self._line_sep = line_sep

    def _iter_unfolded_lines(self):
        """Iter input unfoled lines. Skip comments."""
        line = self._input_file.readline()
        while line:
            line = self._strip_line_sep(line)

            nextline = self._input_file.readline()
            while nextline and nextline[0] == ' ':
                line += self._strip_line_sep(nextline)[1:]
                nextline = self._input_file.readline()

            if not line.startswith('#'):
                yield line
            line = nextline

    def _iter_blocks(self):
        """Iter input lines in blocks separated by blank lines."""
        lines = []
        for line in self._iter_unfolded_lines():
            if line:
                lines.append(line)
            else:
                yield lines
                lines = []

    def _parse_attr(self, line):
        """Parse a single attribute type/value pair."""
        colon_pos = line.index(':')
        attr_type = line[0:colon_pos]
        value_spec = line[colon_pos:colon_pos + 2]
        if value_spec == '::':
            attr_value = base64.decodestring(line[colon_pos + 2:])
        elif value_spec == ':<':
            url = line[colon_pos + 2:].strip()
            attr_value = None
            if self._process_url_schemes:
                u = urlparse(url)
                if u[0] in self._process_url_schemes:
                    attr_value = urlopen(url).read()
        elif value_spec == ':\r\n' or value_spec == '\n':
            attr_value = ''
        else:
            attr_value = line[colon_pos + 2:].lstrip()
        return attr_type, attr_value

    def _check_dn(self, dn, attr_value):
        """Check dn attribute for issues."""
        if dn is not None:
            raise ValueError('Two lines starting with dn: '
                'in one record.')
        if not is_dn(attr_value):
            raise ValueError('No valid string-representation of '
                'distinguished name %s.' % (repr(attr_value)))

    def _check_changetype(self, dn, changetype, attr_value):
        """Check changetype attribute for issues."""
        if dn is None:
            raise ValueError('Read changetype: before getting '
                'valid dn: line.')
        if changetype is not None:
            raise ValueError('Two lines starting with changetype: '
                'in one record.')
        if attr_value not in CHANGE_TYPES:
            raise ValueError('changetype value %s is invalid.'
                % (repr(attr_value)))

    def _parse_record(self, lines):
        """Parse a singel record from a list of lines."""
        dn = None
        changetype = None
        entry = {}

        for line in lines:
            attr_type, attr_value = self._parse_attr(line)

            if attr_type == 'dn':
                self._check_dn(dn, attr_value)
                dn = attr_value
            elif attr_type == 'version' and dn is None:
                pass  # version = 1
            elif attr_type == 'changetype':
                self._check_changetype(dn, changetype, attr_value)
                changetype = attr_value
            elif attr_value is not None and \
                     attr_type.lower() not in self._ignored_attr_types:
                if attr_type in entry:
                    entry[attr_type].append(attr_value)
                else:
                    entry[attr_type] = [attr_value]

        return dn, changetype, entry

    def parse(self):
        """Iterate LDIF records (dn, changetype, entry)."""
        for block in self._iter_blocks():
            yield self._parse_record(block)
