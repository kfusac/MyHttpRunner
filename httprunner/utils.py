# !/usr/bin/python
# -*- coding: utf-8 -*-
import itertools


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
