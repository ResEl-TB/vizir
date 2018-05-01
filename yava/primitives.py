#!/usr/bin/python3

def _(*types):
    return lambda x: isinstance(x, types)

def is_str(x): return _(str)(x)
def is_list(x): return _(list)(x)
def is_dict(x): return _(dict)(x)
