#!/usr/bin/python3

import sys
import os
import yaml
from yava.validator import validate
from yava.primitives import *

files_policy = {"_error": {"@", "plus", "to"},
               "minus": [is_str],
               "plus": [is_str],
               "to": is_str}

policies = {"*": {"_error": {"@", "docs", "locales"},
                  "_warning": {"authors", "code", "copyright", "release", "version"},
                  "authors": is_str, # no list?
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

if len(sys.argv) != 2:
    print("Usage: python3 validator.py <directory>")
    sys.exit(1)

try:
    conf = yaml.load(open(os.path.join(sys.argv[1], ".docs.yml"), 'r'))
except Exception as e:
    print(e)
    sys.exit(1)
else:
    print("ResEl Documentation Validator\n-----------------------------")
    validate(conf, policies)
    print("OK")
