# !/usr/bin/python
# -*- coding: utf-8 -*-

import types


def is_testcase(data_structure):
    '''
    check if data_structure is a testcase.
    Args:
        data_structure (dict): testcase should always be in the following data structure:
            {
                "config":{
                    "name":"desc1",
                    "variables":[], # optional
                    "request":{} # optional
                },
                "teststeps":[
                    teststep1,
                    {   #teststep2
                        "name",
                        "variables":[],
                        "extract":[],
                        "validate":[],
                        "request":{},
                        "function_meta":{}
                    }
                ]
            }
    Returns:
        bool: True if data_structure is valid testcase, otherwise False.
    '''

    if not isinstance(data_structure, dict):
        return False

    if "teststeps" not in data_structure:
        return False

    if not isinstance(data_structure["teststeps"], list):
        return False

    return True


def is_testcases(data_structure):
    '''
    check if data_structure is testcase or testcases list.
    Args:
        data_structure (dict): testcase(s) should always be in the following data structure:
            testcase_dict
            or
            [
                testcase_dict1,
                testcase_dict2
            ]
    Returns:
        bool: True if data_structure is valid testcase(s), otherwise False.
    '''
    if is_testcase(data_structure):
        return True

    if not isinstance(data_structure, list):
        return False

    for item in data_structure:
        if not is_testcase(item):
            return False

    return True


###############################################################################
#   validate variables and functions
###############################################################################
def is_function(tup):
    '''
    Takes (name,object) tuple, return True if it is a function.
    Args:
        tup (tuple): name & specified object
    Returns:
        True if it is a function
    '''
    name, item = tup
    return isinstance(item, types.FunctionType)


def is_variable(tup):
    '''
    Takes (name,object) tuple,return True if it is a variable.
    Args:
        tup (tuple): name & specified object
    Returns:
        True if it is a variable
    '''

    name, item = tup

    if callable(item):
        # function or class
        return False

    if isinstance(item, types.ModuleType):
        # imported module
        return False

    if name.startswith('_'):
        # private property
        return False

    return True
