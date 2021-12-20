# pylint: disable=C0103,C0116,C0321
"""This module provides useful primitives for type comparisons"""


def _(*types):
    """Creates a lambda to check the types of a value against the given types"""
    return lambda x: isinstance(x, types)

def is_str(x): return _(str)(x)
def is_str_or_number(x): return _(float, int, str)(x)
def is_list(x): return _(list)(x)
def is_dict(x): return _(dict)(x)
