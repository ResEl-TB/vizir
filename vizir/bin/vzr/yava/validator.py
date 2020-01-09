# pylint: disable=W0603
"""This module provides the functions to validate a structure against some policies"""


import operator
from functools import reduce

from .primitives import is_list, is_dict
from ..util import err, warn, mag, color_join


POLICIES={}


def brn(named_branch):
    """
    Format a named branch
    :param named_branch: The named branch to format
    """
    return color_join(':', named_branch, mag) or mag('<TOP>')


def get_policies(branch, index = None):
    """
    Get the policies of a branch and, if provided, the policy index to look at
    :param branch: The branch
    :param index: The index
    """
    sub = reduce(operator.getitem, branch, POLICIES)
    if index is None:
        return sub
    return (sub, index if index in sub else '*')


def explore(dic, branch, named_branch):
    """
    Explore a dictionary to performs the checks on its elements
    :param dic: The dictionary to explore
    :param branch: The current
    :param named_branch: The current named branch
    """
    fields = set()
    for i in dic:
        child = check_policies(branch, named_branch, i, dic[i])
        if is_dict(dic[i]):
            # Recursively explore sub-dictionaries
            explore(dic[i], branch + [child], named_branch + [i])
        fields |= {child}
    # At the end, check all the missing fields
    check_missing(branch, named_branch, fields)


def check_policy(rule, value, index, named_branch):
    """
    Check whether a policy is respected by a value
    :param rule: The policy to check
    :param value: The value to check
    :param index: The corresponding index
    :param index: The current named branch
    """
    # Check if we reached a final policy
    if callable(rule):
        if not rule(value):
            err(f'{mag(index)} failed the check {mag(rule.__name__)} in branch {brn(named_branch)}')
    # Else, check if the structures are alike
    else:
        rule_ty = type(rule)
        value_ty = type(value)
        if rule_ty != type([]) and value_ty != rule_ty:
            err(f'{mag(index)} has a structural mismatch (expected {mag(rule_ty.__name__)}, got '
                f'{mag(value_ty.__name__)}) in branch {brn(named_branch)}')


def check_policies(branch, named_branch, index, value):
    """
    Check the policies on a structure
    :param branch: The current branch
    :param named_branch: The current named branch
    :param index: The current index
    :param value: The current value
    """
    (sub, ref) = get_policies(branch, index)

    # If the ref doesn't have a policy
    if ref == '*':
        # If the metapolicy asks to mark it as an error
        if '_error' in sub and '@' in sub['_error']:
            err(f'Unexpected field {mag(index)} in branch {brn(named_branch)}')
        # If the metapolicy asks to mark it as a warning
        elif '_warning' in sub and '@' in sub['_warning']:
            warn(f'Unexpected field {mag(index)} in branch {brn(named_branch)}')

    if is_list(sub[ref]):
        # If both the policy and the value are lists, perform element-wise checks
        if is_list(value):
            for i, val in enumerate(value):
                # If the current element of the value is a dictionary, explore the structure further
                if is_dict(val):
                    explore(val, branch + [index, 0], named_branch + [index, f'#{i}'])
                # Else, perform the final check
                else:
                    check_policy(sub[ref][0], val, index, named_branch + [index, f'#{i}'])
        # If only the policy is a list, consider the value as a 1-element list
        else:
            if is_dict(value):
                explore(value, branch + [index, 0], named_branch + [index, '#'])
            else:
                check_policy(sub[ref][0], value, index, named_branch + [index, '#'])
    else:
        # If both the policy and the value are not lists, simply perform the final check
        check_policy(sub[ref], value, index, named_branch)
    return ref


def missing(fields, policy_fields):
    """
    Lists the fields missing w.r.t. a metapolicy
    :param field: The defined fields
    :param policy_fields: The policy fields
    """
    return policy_fields - fields - {"@"}


def check_missing(branch, named_branch, fields):
    """
    Check the fields missing in the current branch w.r.t. a metapolicy
    :param branch: The current branch
    :param named_branch: The current named branch
    :param fields: The current fields
    """
    sub = get_policies(branch)
    if "_error" in sub:
        miss = missing(fields, sub["_error"])
        if miss:
            field_str = 'field' if len(miss) == 1 else 'fields'
            err(f'Missing {field_str} {color_join(", ", miss, mag)} in branch {brn(named_branch)}')
    if "_warning" in sub:
        miss = missing(fields, sub["_warning"])
        if miss:
            field_str = 'field' if len(miss) == 1 else 'fields'
            warn(f'Missing {field_str} {color_join(", ", miss, mag)} in branch {brn(named_branch)}')


def validate(dic, policies):
    """Validate a dictionary w.r.t. a policy dictionary"""
    global POLICIES
    POLICIES = policies
    return explore(dic, [], [])
