#!/usr/bin/python3

import sys
from functools import reduce
import operator
from .primitives import *

def solve(dict, branch, index = None):
    sub = reduce(operator.getitem, branch, dict)
    if index == None:
        return sub
    return (sub, index if index in sub else "*")

def explore(dic, branch, named_branch, policies, f, g):
    fields = set()
    for i in dic:
        child = f(policies, branch, named_branch, i, dic[i])
        if isinstance(dic[i], dict):
            explore(dic[i], branch + [child], named_branch + [i], policies, f, g)
        fields |= {child}
    g(policies, branch, named_branch, fields)

def final(rule, value, index, named_branch):
    c = callable(rule)
    if c == is_dict(value) or c and not rule(value):
        print("ERROR: {} failed the check {} in branch {}".format(index, rule.__name__ if c else "is_dict", ":".join(named_branch)))
        sys.exit(1)

def check_policies(policies, branch, named_branch, index, value):
    (sub, ref) = solve(policies, branch, index)
    if ref == "*":
        if "_error" in sub and "@" in sub["_error"]:
            print("ERROR: Unexpected field: {} in branch {}".format(index, ":".join(named_branch)))
            sys.exit(1)
        elif "_warning" in sub and "@" in sub["_warning"]:
            print("WARNING: Unexpected field: {} in branch {}".format(index, ":".join(named_branch)))
    if ref in sub:
        if is_list(sub[ref]):
            if is_list(value):
                for i in range(len(value)):
                    if is_dict(value[i]):
                        explore(value[i], branch + [index, 0], named_branch + [index, "#{}".format(i)], policies, check_policies, check_missing)
                    else:
                        final(sub[ref][0], value[i], index, named_branch + [index, "#{}".format(i)])
            else:
                if is_dict(value):
                    explore(value, branch + [index, 0], named_branch + [index, "#"], policies, check_policies, check_missing)
                else:
                    final(sub[ref][0], value, index, named_branch + [index, "#"])
        else:
            final(sub[ref], value, index, named_branch)
    return ref

def missing(fields, policy_fields):
    return policy_fields - fields - {"@"};

def check_missing(policies, branch, named_branch, fields):
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

def validate(dic, policies):
    return explore(dic, [], [], policies, check_policies, check_missing)
