#!/usr/bin/python3

import sys
import os
import yaml
from functools import reduce
import operator

def _(*types):
    return lambda x: isinstance(x, types)

_str = _(str)
_str.__name__ = "_str"
def _str_list(x):
    return bool(x) and all(_str(e) for e in x)

def solve(dict, branch, index = None):
    sub = reduce(operator.getitem, branch, dict)
    if index == None:
        return sub
    return (sub, index if index in sub else "*")

def explore(dic, branch, named_branch, f, g):
    fields = set()
    for i in dic:
        child = f(branch, named_branch, i, dic[i])
        if isinstance(dic[i], dict):
            explore(dic[i], branch + [child], named_branch + [i], f, g)
        fields |= {child}
    g(branch, named_branch, fields)

policies = {"*": {"_error": {"@", "docs", "locales"},
                  "_warning": {"authors", "code", "copyright", "release", "version"},
                  "authors": _str, # no list?
                  "code": {"*": {"_error": {"@", "plus"},
                                 "_warning": {"templates"},
                                 "from": _str,
                                 "minus": _str_list,
                                 "plus": _str_list,
                                 "templates": _str_list}},
                  "copyright": _str,
                  "docs": {"_error": {"@", "plus"},
                           "from": _str,
                           "minus": _str_list,
                           "plus": _str_list},
                  "locales": _str_list,
                  "release": _str,
                  "version": _str}}

def check_policies(branch, named_branch, index, value):
    global policies
    (sub, ref) = solve(policies, branch, index)
    if ref == "*":
        if "_error" in sub and "@" in sub["_error"]:
            print("ERROR: Unexpected field: {} in branch {}".format(index, ":".join(named_branch)))
            sys.exit(1)
        elif "_warning" in sub and "@" in sub["_warning"]:
            print("WARNING: Unexpected field: {} in branch {}".format(index, ":".join(named_branch)))
    if ref in sub:
        c = callable(sub[ref])
        if c == isinstance(value, dict) or c and not sub[ref](value):
            print("ERROR: {} failed the check {} in branch {}".format(index, sub[ref].__name__ if c else "_dict", ":".join(named_branch)))
            sys.exit(1)
    return ref

def missing(fields, policy_fields):
    return policy_fields - fields - {"@"};

def check_missing(branch, named_branch, fields):
    global policies
    sub = solve(policies, branch)
    if "_error" in sub:
        m = missing(fields, sub["_error"])
        if m:
            print("ERROR: Missing field(s): {} in branch {}".format(", ".join(m), ":".join(named_branch)))
            sys.exit(1)
    if "_warning" in sub:
        m = missing(fields, sub["_warning"])
        if m:
            print("WARNING: Missing field(s): {} in branch {}".format(", ".join(m), ":".join(named_branch)))

print("ResEl Documentation Validator\n-----------------------------")

if len(sys.argv) != 2:
    print("Usage: python3 validator.py <directory>")
    sys.exit(1)

try:
    conf = yaml.load(open(os.path.join(sys.argv[1], ".docs.yml"), 'r'))
except Exception as e:
    print(e)
    sys.exit(1)
else:
    explore(conf, [], [], check_policies, check_missing)
    print("OK")
