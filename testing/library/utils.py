#!/usr/bin/env python3
"""This module provides a class and a few functions for handling XML files within the Robot Framework."""

from jinja2 import Template
from difflib import HtmlDiff, unified_diff
from lxml import html as html_parser, etree
from ipaddress import ip_interface
from robot.libraries.BuiltIn import BuiltIn

import re
import os


class ServiceElement(etree.ElementBase):
    """This subclass provides methods supporting data transformation and retrieval from the input XML string."""

    @property
    def package(self):
        """Returns the unqualified tag of the element."""
        return etree.QName(self).localname

    @property
    def netmask(self):
        """Returns the subnet mask of current element."""
        return ip_interface(self.text).netmask

    @property
    def ip(self):
        """Returns the IP address of current element."""
        return ip_interface(self.text).ip

    @property
    def xml_string(self):
        """Renders the current element (and all child elements) as a XML string."""
        return etree.tostring(self).decode('utf-8')

    @property
    def sanitized_text(self):
        """Returns the sanitized text of current element by replacing any occurances of <period> <left parentheses>"""
        """<right parentheses> <comma> <space> characters with an <underscore>."""
        return re.sub(r'[\.\(\)\, ]', '_', self.text)

    def xpath(self, _path, namespaces=None, **kwargs):
        """The lxml library does not support default namespaces. This method wraps the xpath method of the parent"""
        """class to add this functionality."""
        if namespaces is None:
            namespaces = {}

        namespaces.update({'default': etree.QName(self).namespace})
        no_ns_match = re.compile(r'/(?![^\/\:]+\:)')

        _path = no_ns_match.sub('/default:', _path)

        return super().xpath(_path, namespaces=namespaces, **kwargs)

DEFAULT_PARSER = etree.XMLParser(remove_blank_text=True)
DEFAULT_PARSER.set_element_class_lookup(
    etree.ElementDefaultClassLookup(element=ServiceElement)
)

def Service_Instance_Keystring(inst, key_nodes):
    """Returns a key string from the specified key xml nodes."""
    keys = [inst.xpath(f'string(/{inst.package}/{key})') for key in key_nodes]

    return str.join(',', keys)

def normalize_xml(xml_string):
    """Normalize and pretty print an imput XML string."""
    tree = etree.fromstring(xml_string, DEFAULT_PARSER)

    return etree.tostring(tree, pretty_print=True).decode("utf-8")

def _html_add_css(html_diff):
    """Customizes the CSS of the HTML side by side comparison diff."""
    html_diff = html_parser.fromstring(html_diff)

    diff_chg = html_diff.find_class('diff_chg')
    diff_add = html_diff.find_class('diff_add')
    diff_sub = html_diff.find_class('diff_sub')

    for diff in diff_chg + diff_add + diff_sub:
        row = diff.getparent().getparent()
        if 'diff_row' not in row.classes:
            row.classes.add('diff_row')

    style_element = html_parser.HtmlElement(
        "table.diff tr.diff_row span.diff_chg { background-color: #ff4040; }"
        "table.diff tr.diff_row span.diff_add { background-color: #ff4040; }"
        "table.diff tr.diff_row span.diff_sub { background-color: #ff4040; }"
        "table.diff tr.diff_row:hover { background-color: rgba(255, 150, 150, 0.7); }"
        "table.diff tr.diff_row { background-color: rgba(255, 150, 150, 1); }"
        "table.diff tr:hover { background-color: rgba(157, 210, 225, 0.7); }"
        "table.diff tr { background-color: rgba(157, 210, 225, 1); }"
    )

    style_element.tag = 'style'

    html_diff.insert(0, style_element)

    return html_parser.tostring(html_diff).decode('utf-8')

def Render_Template(template_file, **kargs):
    """Returns a Jinja2 rendering of the specified template file and variables as a string."""

    return Template(open(template_file).read()).render(**kargs)

def Validate_Response(received, expected):
    """Returns a boolean True or False based on whether the received XML matches the expected XML."""
    received = normalize_xml(received).splitlines()
    expected = normalize_xml(expected).splitlines()

    for _ in unified_diff(received, expected):
        builtin_scope = BuiltIn()

        test_name = builtin_scope.get_variable_value('${TEST NAME}')
        crud_test = builtin_scope.get_variable_value('${CRUD_TEST}')

        html_diff = HtmlDiff(tabsize=4).make_table(received, expected, fromdesc='Received', todesc='Expected', context=True, numlines=10)
        html_diff = _html_add_css(html_diff)
        builtin_scope.log(f"{test_name} {crud_test}: Validate Response Failed", level='ERROR')
        builtin_scope.log(html_diff, html=True)
        builtin_scope.fail(f"{test_name} {crud_test}: Validate Response Failed")

    return True

def Service_Instance(xml_string):
    """Parses the input string and returns an instance of the ServiceElement class."""

    return etree.fromstring(xml_string, DEFAULT_PARSER)

def find_all(pattern, path):
    """Returns a list of strings containing files matching the input regex pattern."""
    result = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if re.findall(pattern, file):
                result.append(os.path.join(root, file))
            for dir in dirs:
                result.extend(find_all(pattern, dir))

    return result

def pp_xml(xmls):
    """Normalizes and pretty prints the test XML files in place."""
    for xml in xmls:
        print(xml)
        x = open(xml).read()
        x = normalize_xml(x)
        with open(xml, 'w') as f:
            f.write(x)


if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'normalize_tests':
        test_xml = find_all(r'(create|read|update|delete).*\.xml', '.')
        pp_xml(test_xml)
