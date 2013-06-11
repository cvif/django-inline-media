#!/usr/bin/env python

import sys
sys.path.insert(0, '../..') # parent of inline_media directory
sys.path.insert(0, '..')

import os
os.environ["DJANGO_SETTINGS_MODULE"] = "demo.settings"

from django.core.management import execute_from_command_line
import imp
try:
    imp.find_module('settings') # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
    sys.exit(1)

import settings

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
