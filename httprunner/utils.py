# !/usr/bin/python
# -*- coding: utf-8 -*-
import itertools
import os
from collections import OrderedDict

from httprunner import logger


def set_os_environ(variables_mapping):
    '''
    set variables mapping to os.environ
    '''

    for variable in variables_mapping:
        os.environ[variable] = variables_mapping[variable]
        logger.log_debug(f'Loaded variable: {variable}')


def gen_cartesian_product(*args):
    '''
    generate cartesian product for lists
    Args:
        args (list): e.g.
            [{"a":1,"a":2}],
            [
                {"x":111,"y":112},
                {"x":121,"y":122}
            ]
    Returns:
        cartesian product in list
        [
            {"a":1,"x":111,"y":112},
            {"a":1,"x":121,"y":122},
            {"a":2,"x":111,"y":112},
            {"a":2,"x":121,"y":122}
        ]
    '''

    if not args:
        return []
    elif len(args) == 1:
        return args[0]

    product_list = []
    for product_item_tuple in itertools.product(*args):
        product_item_dict = {}
        for item in product_item_tuple:
            product_item_dict.update(item)

        product_list.append(product_item_dict)

    return product_list


def convert_mappinglist_to_OrderedDict(mapping_list):
    '''
    convert mapping list to ordered dict
    Args:
        mapping_list (list):
            [
                {'a':1},
                {'b':2}
            ]
    Returns:
        OrderedDict: converted mapping to OrderedDict
            OrderedDict(
                {
                    'a':1,
                    'b':2
                }
            )
    '''

    ordered_dict = OrderedDict()
    for map_dict in mapping_list:
        OrderedDict.update(map_dict)

    return ordered_dict


def deep_update_dict(origin_dict, override_dict):
    '''
    update origin dict with override dict recursively
        e.g.    origin_dict = {'a': 1, 'b': {'c': 2, 'd': 4}}
                override_dict = {'b': {'c': 3}}
        return: {'a':1, 'b': {'c': 3, 'd': 4}}
    '''

    if not override_dict:
        return origin_dict

    for key, value in override_dict.items():
        if isinstance(value, dict):
            tmp = deep_update_dict(origin_dict.get(key, {}), value)
            origin_dict[key] = tmp
        elif value is None:
            continue
        else:
            origin_dict[key] = override_dict[key]

    return origin_dict


def get_uniform_comparator(comparator):
    '''
    convert comparator alias to uniform name
    '''

    if comparator in ['eq', 'equals', '==', 'is']:
        return 'equals'
    elif comparator in ['lt', 'less_than']:
        return 'less_than'
    elif comparator in ['le', 'less_than_or_equals']:
        return 'less_than_or_equals'
    elif comparator in ['gt', 'greater_than']:
        return 'greater_than'
    elif comparator in ['ge', 'greater_than_or_equals']:
        return 'greater_than_or_equals'
    elif comparator in ['ne', 'not_equals', '!=']:
        return 'not_equals'
    elif comparator in ['str_eq', 'string_equals']:
        return 'string_equals'
    elif comparator in ['len_eq', 'length_equals', 'count_eq']:
        return 'length_equals'
    elif comparator in [
            'len_gt', 'count_gt', 'length_greater_than', 'count_greater_than'
    ]:
        return 'length_greater_than'
    elif comparator in [
            'len_ge', 'count_ge', 'length_greater_than_or_equals',
            'count_greater_than_or_equals'
    ]:
        return 'length_greater_than_or_equals'
    elif comparator in [
            'len_lt', 'count_lt', 'length_less_than', 'count_less_than'
    ]:
        return 'length_less_than'
    elif comparator in [
            'len_le', 'count_le', 'length_less_than_or_equals',
            'count_less_than_or_equals'
    ]:
        return 'length_less_than_or_equals'
    else:
        return comparator