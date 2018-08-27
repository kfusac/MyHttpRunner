# !/usr/bin/python
# -*- coding: utf-8 -*-

import ast
import os
import re

from httprunner import exceptions, utils

variable_regexp = r"\$([\w_]+)"
function_regexp = r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}"
funciton_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\.\-/_ =,]*)\)$")

###############################################################################
#   expression parser
###############################################################################


def parse_string_value(str_value):
    '''
    parse string to number if possible
    e.g.
        "123" => 123
        "12.2" => 12.2
        "abc" => "abc"
        "$var" => "$var"
    '''
    try:
        return ast.literal_eval(str_value)
    except ValueError:
        return str_value
    except SyntaxError:
        # e.g. $var, ${func}
        return str_value


def extract_variables(content):
    '''
    extract all variables names from content, which is in format $variable
    Args:
        content (str): string content
    Returns:
        list: variables list extracted from string content
    Examples:
        >>> extract_variables("$variable")
        ["variable"]
        >>> extract_variables("/blog/$postid")
        ["postid"]
        >>> extract_variables("/$var1/$var2")
        ["var1", "var2]
        >>> extract_variables("abc")
        []
    '''
    try:
        return re.findall(variable_regexp, content)
    except TypeError:
        return []


def extract_functions(content):
    '''
    extract all functions from string content, which are in format ${func()}
    Args:
        content (str): string content
    Returns:
        list: functions list extracted from string content
    Examples:
        >>> extract_functions("${func(5)}")
        ["func(5)"]
        >>> extract_functions("${func(a=1, b=2)}")
        ["func(a=1, b=2)"]
        >>> extract_functions("/api/1000?_t=${get_timestamp()}")
        ["get_timestamp()"]
        >>> extract_functions("/api/${add(1, 2)}")
        ["add(1, 2)"]
        >>> extract_functions("/api/${add(1 ,2)}?_t=${get_timestamp()}")
        ["add(1, 2)", "get_timestamp()"]
    '''

    try:
        return re.findall(function_regexp, content)
    except TypeError:
        return []


def parse_function(content):
    '''
    parse function name and args from string expression
    Args:
        content (str): string content
    Returns:
        dict: function meta dict
            {
                "func_name":"xxx",
                "args":[],
                "kwargs":{}
            }
    Examples:
        >>> parse_function("func()")
        {'func_name': 'func','args': [],'kwargs': {}}
        >>> parse_function("func(5)")
        {'func_name': 'func','args': [5],'kwargs': {}}
        >>> parse_function("func(1, 2)")
        {'func_name': 'func','args': [1, 2],'kwargs': {}}
        >>> parse_function("func(a=1, b=2)")
        {'func_name': 'func','args': [],'kwargs': {'a': 1, 'b': 2}}
        >>> parse_function("func(1, 2, a=3, b=4)")
        {'func_name': 'func','args': [1, 2],'kwargs': {'a': 3, 'b': 4}}
    '''

    matched = funciton_regexp_compile.match(content)

    if not matched:
        raise exceptions.FunctionNotFound(f'{content} not found!')

    function_meta = {"func_name": matched.group(1), "args": [], "kwargs": {}}
    args_str = matched.group(2).strip()
    if args_str == "":
        return function_meta

    args_list = args_str.split(',')
    for arg in args_list:
        arg = arg.strip()
        if "=" in arg:
            key, value = arg.split("=")
            function_meta["kwargs"][key.strip()] = parse_string_value(
                value.strip())
        else:
            function_meta["args"].append(parse_string_value(arg))

    return function_meta


def parse_validator(validator):
    '''
    parse validator, validator maybe in two format
    Args:
        validator (dict):
            format1:
                {"check":"status_code","comparator":"eq","expect":201}
                {"check":"$resp_body_success","comparator":"eq","expect":True}
            format2:
                {"eq":["status_code",201]}
                {"eq":["$resp_body_success",True]}
    Returns:
        dict: validator info
            {
                "check":"status_code",
                "expect":201,
                "comparator":"eq"
            }
    '''
    if not isinstance(validator, dict):
        raise exceptions.ParamError(f'invalid validator: {validator}')

    if "check" in validator and len(validator) > 1:
        check_item = validator.get("check")

        if "expect" in validator:
            expect_value = validator.get("expect")
        elif "expected" in validator:
            expect_value = validator.get("expected")
        else:
            raise exceptions.ParamError(f"invalid validator: {validator}")

        comparator = validator.get("comparator", "eq")
    elif len(validator) == 1:
        comparator = list(validator.keys())[0]
        compare_values = validator[comparator]

        if not isinstance(compare_values, list) or len(compare_values) != 2:
            raise exceptions.ParamError(f"invalid validator: {validator}")

        check_item, expect_value = compare_values
    else:
        raise exceptions.ParamError(f"invalid validator: {validator}")

    return {
        "check": check_item,
        "expect": expect_value,
        "comparator": comparator
    }


def parse_parameters(parameters, variables_mapping, functions_mapping):
    '''
    parse parameters and generate cartesian product
    Args:
        parameters (list):parameter name and value in list
            parameter value may be in three types:
                (1) data list: e.g. ['ios/10.1', 'ios/10.2', 'ios/10.3']
                (2) call built-in parameterize function, "${parameter(account.csv)}"
                (3) call custom function in confcustom.py, ${gen_app_version()}
        variables_mapping (dict): variables mapping loaded from confcustom.py
        functions_mapping (dict): functions mapping loaded from confcustom.py
    Returns:
        list: cartesian product list
    Examples:
        >>> parameters = [
            {'user_agent':['ios/10.1', 'ios/10.2', 'ios/10.3']},
            {'username-password}: "${parameterize(account.csv)}",
            {'app_verison': '${gen_app_version()}'}
        ]
        >>> parse_parameters(parameters)
    '''
    parsed_parameters_list = []
    for parameter in parameters:
        parameter_name, parameter_content = list(parameter.items())[0]
        parameter_name_list = parameter_name.split('-')

        if isinstance(parameter_content, list):
            # (1) data list
            # e.g. {'app_version':['2.8.5','2.8.6]}
            #      => [{'app_version':'2.8.5','app_version':'2.8.6'}]
            # e.g. {'username-password':[['user1','111111'],['user2','222222']]}
            #      => [{'username':'user1','password':'111111'},{'username':'user2','password':'222222'}]
            parameter_content_list = []
            for parameter_item in parameter_content:
                if not isinstance(parameter_item, (list, tuple)):
                    # '2.8.5' => ['2.8.5']
                    parameter_item = [parameter_item]
                    # ['app_version'],['2.8.5']=>{'app_version':'2.8.5'}
                parameter_content_dict = dict(
                    zip(parameter_name_list, parameter_item))
                parameter_content_list.append(parameter_content_dict)
        else:
            # (2) & (3)
            parsed_parameter_content = parse_data(
                parameter_content, variables_mapping, functions_mapping)
            if not isinstance(parsed_parameter_content, list):
                raise exceptions.ParamError(
                    f'{parameters} parameters syntax error!')

            parameter_content_list = [{
                key: parameter_item[key]
                for key in parameter_name_list
            } for parameter_item in parsed_parameter_content]

        parsed_parameters_list.append(parameter_content_list)
    return utils.gen_cartesian_product(*parsed_parameters_list)


###############################################################################
#   content parser
###############################################################################


def substitute_variables(content, variables_mapping):
    '''
    subsititute variables in content with variables_mapping
    Args:
        content (str/dict/list/numeric/bool/type): content to be substituted.
        variables_mapping (dict): variables mapping.
    Returns:
        subsitituted content.
    Examples:
        >>> content = {
                'request': {
                    'url': '/api/users/$uid',
                    'headers': {'token': '$token'}
                }
            }
        >>> variables_mapping = {"$uid": 1000}
        >>> substitute_variables(content, variables_mapping)
            {
                'request': {
                    'url': '/api/users/1000',
                    'headers': {'token': '$token'}
                }
            }
    '''

    if isinstance(content, (list, set, tuple)):
        return [
            substitute_variables(item, variables_mapping) for item in content
        ]
    if isinstance(content, dict):
        return {
            substitute_variables(key, variables_mapping): substitute_variables(
                value, variables_mapping)
            for key, value in content.items()
        }

    if isinstance(content, str):
        # content is in string format
        for var, value in variables_mapping.items():
            if content == var:
                content = value
            else:
                if not isinstance(value, str):
                    value = str(value)
                content = content.replace(var, value)

    return content


def get_mapping_variable(variable_name, variables_mapping):
    '''
    get variable from variables_mapping
    Args:
        variable_name (str): specified variable name
        variables_mapping (dict): variables mapping
    Returns:
        mapping variable value.
    Raises:
        exceptions.VariableNotFound: variable is not found
    '''

    try:
        return variables_mapping[variable_name]
    except KeyError:
        raise exceptions.VariableNotFound(f'{variable_name} is not found.')


def get_mapping_funciton(function_name, functions_mapping):
    '''
    get function from functions_mapping, if not found, then try to check if builtin function.
    Args:
        function_name (str): specified function name
        functions_mapping (dict): functions mapping
    Returns:
        mapping function object
    Raises:
        exceptions.FunctionNotFound: function is neither defined in confcustom.py nor builtin.
    '''

    if function_name in functions_mapping:
        return functions_mapping[function_name]

    try:
        # check if built-in functions
        item_func = eval(function_name)
        if callable(item_func):
            return item_func
    except (NameError, TypeError):
        raise exceptions.FunctionNotFound(f'{function_name} is not found.')


def parse_string_functions(content, variables_mapping, functions_mapping):
    '''
    parse string content with functions mapping.
    Args:
        content (str): string content to be parsed.
        variables_mapping (dict): variables_mapping
        functions_mapping (dict): functions_mapping
    Returns:
        str: parsed string content
    Examples:
        >>> content = "abc${add_one(3)}def"
        >>> functions_mapping = {"add_one": lambda x: x + 1}
        >>> parse_string_functions(content,functions_mapping)
            "abc4def
    '''
    functions_list = extract_functions(content)
    for func_content in functions_list:
        function_meta = parse_function(func_content)
        func_name = function_meta['func_name']
        args = function_meta.get("args", [])
        kwargs = function_meta.get('kwargs', {})
        args = parse_data(args, variables_mapping, functions_mapping)
        kwargs = parse_data(kwargs, variables_mapping, functions_mapping)

        if func_name in ["parameterize", 'P']:
            from httprunner import loader
            eval_value = loader.load_csv_file(*args, **kwargs)
        else:
            func = get_mapping_funciton(func_name, functions_mapping)
            eval_value = func(*args, **kwargs)

        func_content = "${" + func_content + "}"
        if func_content == content:
            # content is a function
            content = eval_value
        else:
            # content contains one or many functions
            content = content.replace(func_content, str(eval_value), 1)
    return content


def parse_string_variables(content, variables_mapping):
    '''
    parse string content with variables mapping.
    Args:
        content (str): string content to be parsed.
        variables_mapping (dict): variables mappings.
    Returns:
        str: parsed string content
    Examples:
        >>> content = '/api/users/$uid"
        >>> variables_mapping = {"$uid": 1000}
        >>> parse_string_variables(content, variables_mapping)
            "/api/users/1000"
    '''
    variables_list = extract_variables(content)
    for variable_name in variables_list:
        variable_value = get_mapping_variable(variable_name, variables_mapping)

        if f'${variable_name}' == content:
            # content is a variable
            content = variable_value
        else:
            # content contains one or several variabels
            if not isinstance(variable_value, str):
                variable_value = str(variable_value)
            content = content.replace(f'${variable_name}', variable_value, 1)
    return content


def parse_data(content, variables_mapping=None, functions_mapping=None):
    '''
    Args:
        content (str/dict/list/numeric/bool/type): content to be parsed
        variables_mapping (dict): variables mapping.
        functions_mapping (dict): functions mapping.
    Returns:
        parsed content.
    Examples:
        >>> content = {
                'request': {
                    'url': '/api/users/$uid',
                    'headers': {'token': '$token'}
                }
            }
        >>> variables_mapping = {"$uid": 1000}
        >>> parse_data(content, variables_mapping)
            {
                'request': {
                    'url': '/api/users/1000',
                    'headers': {'token': '$token'}
                }
            }
    '''

    if content is None or isinstance(content, (int, float, bool, type)):
        return content

    if isinstance(content, (list, set, tuple)):
        return [
            parse_data(item, variables_mapping, functions_mapping)
            for item in content
        ]

    if isinstance(content, dict):
        return {
            parse_data(key, variables_mapping, functions_mapping): parse_data(
                value, variables_mapping, functions_mapping)
            for key, value in content.items()
        }

    if isinstance(content, str):
        variables_mapping = variables_mapping or []
        functions_mapping = functions_mapping or {}
        content = content.strip()

        # replace functions with evaluated value
        content = parse_string_functions(content, variables_mapping,
                                         functions_mapping)

        # replace vairables with binding value
        content = parse_string_variables(content, variables_mapping)

    return content
