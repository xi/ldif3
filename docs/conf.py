# -*- coding: utf-8 -*-
import sys
import os
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))


def get_meta(key):
    cmd = ['python', '../setup.py', '--' + key]
    return subprocess.check_output(cmd).rstrip()


extensions = [
    'sphinx.ext.autodoc',
]
master_doc = 'index'

project = get_meta('name')
copyright = u'2015, ' + get_meta('author')
version = get_meta('version')
