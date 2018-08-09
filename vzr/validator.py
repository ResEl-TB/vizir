#!/usr/bin/python3

import sys
import os
import yaml
from .yava.validator import validate as _validate
from .yava.primitives import *

files_policy = {"_error": {"@", "plus", "to"},
               "minus": [is_str],
               "plus": [is_str],
               "to": is_str}

policies = {"*": {"_error": {"@", "docs", "locales", "version"},
                  "_warning": {"code", "copyright", "release"},
                  "code": {"*": {"_error": {"@"},
                                 "_warning": {"templates"},
                                 "files": [files_policy],
                                 "from": is_str,
                                 "templates": [is_str]}},
                  "copyright": is_str,
                  "docs": {"_error": {"@"},
                           "files": [files_policy],
                           "from": is_str},
                  "locales": [is_str],
                  "release": is_str,
                  "version": is_str}}

def validate(directory="."):
    try:
        conf = yaml.load(open(os.path.join(directory, ".docs.yml"), 'r'))
    except Exception as e:
        print(e)
        sys.exit(1)

    print("ResEl Documentation Validator\n-----------------------------")
    _validate(conf, policies)
    print("OK")
