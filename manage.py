#!/usr/bin/env python
import os
import sys
from django.core.management import execute_from_command_line
sys.dont_write_bytecode = True

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    except Exception as e:
        print(e)
        print("There was an error loading django modules. Do you have django installed?")
        sys.exit()
