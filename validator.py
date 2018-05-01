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
_list = _(list)
_list.__name__ = "_list"
_dict = _(dict)
_dict.__name__ = "_dict"

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

files_policy = {"_error": {"@", "plus", "to"},
               "minus": [_str],
               "plus": [_str],
               "to": _str}

policies = {"*": {"_error": {"@", "docs", "locales"},
                  "_warning": {"authors", "code", "copyright", "release", "version"},
                  "authors": _str, # no list?
                  "code": {"*": {"_error": {"@"},
                                 "_warning": {"templates"},
                                 "files": [files_policy],
                                 "from": _str,
                                 "templates": [_str]}},
                  "copyright": _str,
                  "docs": {"_error": {"@"},
                           "files": [files_policy],
                           "from": _str},
                  "locales": [_str],
                  "release": _str,
                  "version": _str}}

def final(rule, value, index, named_branch):
    c = callable(rule)
    if c == _dict(value) or c and not rule(value):
        print("ERROR: {} failed the check {} in branch {}".format(index, rule.__name__ if c else "_dict", ":".join(named_branch)))
        sys.exit(1)

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
        if _list(sub[ref]):
            if _list(value):
                for i in range(len(value)):
                    if _dict(value[i]):
                        explore(value[i], branch + [index, 0], named_branch + [index, "#{}".format(i)], check_policies, check_missing)
                    else:
                        final(sub[ref][0], value[i], index, named_branch + [index, "#{}".format(i)])
            else:
                if _dict(value):
                    explore(value, branch + [index, 0], named_branch + [index, "#"], check_policies, check_missing)
                else:
                    final(sub[ref][0], value, index, named_branch + [index, "#"])
        else:
            final(sub[ref], value, index, named_branch)
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
