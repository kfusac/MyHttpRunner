# !/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import pytest

from httprunner import exceptions, loader, parser


class TestParser:
    def test_parse_string_value(self):
        assert parser.parse_string_value("123") == 123
        assert parser.parse_string_value("12.2") == 12.2
        assert parser.parse_string_value("abc") == "abc"
        assert parser.parse_string_value("$var") == "$var"
        assert parser.parse_string_value("${func}") == "${func}"

    def test_extract_variables(self):
        assert parser.extract_variables("$var") == ["var"]
        assert parser.extract_variables("$var123") == ["var123"]
        assert parser.extract_variables("$var_name") == ["var_name"]
        assert parser.extract_variables("var") == []
        assert parser.extract_variables("a$var") == ["var"]
        assert parser.extract_variables("$v ar") == ["v"]
        assert parser.extract_variables("$abc*") == ["abc"]
        assert parser.extract_variables("${func()}") == []
        assert parser.extract_variables("${func(1,2)}") == []
        assert parser.extract_variables(
            "${gen_md5($TOKEN, $data, $random)}") == [
                "TOKEN", "data", "random"
            ]

    def test_extract_functions(self):
        assert parser.extract_functions("${func()}") == ["func()"]
        assert parser.extract_functions("${func(5)}") == ["func(5)"]
        assert parser.extract_functions("${func(a=1, b=2)}") == [
            "func(a=1, b=2)"
        ]
        assert parser.extract_functions("${func(1, $b, c=$x, d=4)}") == [
            "func(1, $b, c=$x, d=4)"
        ]
        assert parser.extract_functions(
            "$/api/1000?_t=${get_timestamp()}") == ["get_timestamp()"]
        assert parser.extract_functions("${/api/${add(1, 2)}}") == [
            "add(1, 2)"
        ]
        assert parser.extract_functions(
            "$/api/${add(1, 2)}?_t=${get_timestamp()}") == [
                "add(1, 2)", "get_timestamp()"
            ]
        assert parser.extract_functions("abc${func(1, 2, a=3, b=4)}def") == [
            "func(1, 2, a=3, b=4)"
        ]

    def test_parse_function(self):
        assert parser.parse_function("func()") == {
            'func_name': 'func',
            'args': [],
            'kwargs': {}
        }
        assert parser.parse_function("func(5)") == {
            'func_name': 'func',
            'args': [5],
            'kwargs': {}
        }
        assert parser.parse_function("func(1, 2)") == {
            'func_name': 'func',
            'args': [1, 2],
            'kwargs': {}
        }
        assert parser.parse_function("func(a=1,b=2)") == {
            'func_name': 'func',
            'args': [],
            'kwargs': {
                'a': 1,
                'b': 2
            }
        }
        assert parser.parse_function("func(a=1, b =2)") == {
            'func_name': 'func',
            'args': [],
            'kwargs': {
                'a': 1,
                'b': 2
            }
        }
        assert parser.parse_function("func(1, 2, a=3, b=4)") == {
            'func_name': 'func',
            'args': [1, 2],
            'kwargs': {
                'a': 3,
                'b': 4
            }
        }
        assert parser.parse_function("func($request,123)") == {
            'func_name': 'func',
            'args': ['$request', 123],
            'kwargs': {}
        }
        assert parser.parse_function("func( )") == {
            'func_name': 'func',
            'args': [],
            'kwargs': {}
        }
        assert parser.parse_function("func(hello world, a=3, b=4)") == {
            'func_name': 'func',
            'args': ['hello world'],
            'kwargs': {
                'a': 3,
                'b': 4
            }
        }
        assert parser.parse_function("func($request, 12.3)") == {
            'func_name': 'func',
            'args': ['$request', 12.3],
            'kwargs': {}
        }

    def test_parse_validator(self):
        validator = {'check': 'status_code', 'comparator': 'eq', 'expect': 200}
        assert parser.parse_validator(validator) == {
            'check': 'status_code',
            'comparator': 'eq',
            'expect': 200
        }
        validator = {'eq': ['status_code', 200]}
        assert parser.parse_validator(validator) == {
            'check': 'status_code',
            'comparator': 'eq',
            'expect': 200
        }

    def test_parse_data(self):
        content = {
            'request': {
                'url': '/api/users/$uid',
                'method': '$method',
                'header': {
                    'token': '$token'
                },
                'data': {
                    'null': None,
                    'true': True,
                    'false': False,
                    'empty_str': '',
                    'value': 'abc${add_one(3)}def'
                }
            }
        }
        variables_mapping = {'uid': 1000, 'method': 'POST', 'token': 'abc123'}
        functions_mapping = {'add_one': lambda x: x + 1}
        result = parser.parse_data(content, variables_mapping,
                                   functions_mapping)
        assert result['request']['url'] == '/api/users/1000'
        assert result['request']['header']['token'] == 'abc123'
        assert result['request']['method'] == 'POST'
        assert result['request']['data']['null'] is None
        assert result['request']['data']['true']
        assert not result['request']['data']['false']
        assert result['request']['data']['empty_str'] == ''
        assert result['request']['data']['value'] == 'abc4def'

    def test_parse_data_variables(self):
        variables_mapping = {
            'var_1': 'abc',
            'var_2': 'def',
            'var_3': 123,
            'var_4': {
                'a': 1
            },
            'var_5': True,
            'var_6': None
        }
        assert parser.parse_data('$var_1', variables_mapping) == 'abc'
        assert parser.parse_data('var_1', variables_mapping) == 'var_1'
        assert parser.parse_data('$var_1#XYZ', variables_mapping) == 'abc#XYZ'
        assert parser.parse_data('/$var_1/$var_2/$var_3',
                                 variables_mapping) == '/abc/def/123'
        assert parser.parse_string_variables(
            '${func($var_1,$var_2,xyz)}',
            variables_mapping) == '${func(abc,def,xyz)}'
        assert parser.parse_data('$var_3', variables_mapping) == 123
        assert parser.parse_data('$var_4', variables_mapping) == {'a': 1}
        assert parser.parse_data('$var_5', variables_mapping)
        assert parser.parse_data('$var_6', variables_mapping) is None
        assert parser.parse_data(["$var_1", "$var_2"],
                                 variables_mapping) == ['abc', 'def']
        assert parser.parse_data({
            "$var_1": "$var_2"
        }, variables_mapping) == {
            'abc': 'def'
        }

    def test_parse_data_multiple_identical_variables(self):
        variables_mapping = {'user_id': 100, 'data': 1498}
        content = '/users/$user_id/traning/$data?user_Id=$user_id&data=$data'
        assert parser.parse_data(
            content, variables_mapping
        ) == '/users/100/traning/1498?user_Id=100&data=1498'

        variables_mapping = {'user': 100, 'userid': 1000, 'data': 1498}
        content = '/users/$user/$userid/$data?userId=$userid&data=$data'
        assert parser.parse_data(
            content,
            variables_mapping) == '/users/100/1000/1498?userId=1000&data=1498'

    def test_parse_data_functions(self):
        import random, string
        gen_random_string = lambda str_len: ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(str_len))
        functions_mapping = {'gen_random_string': gen_random_string}
        result = parser.parse_data(
            '${gen_random_string(5)}', functions_mapping=functions_mapping)
        assert len(result) == 5

        add_two_nums = lambda a, b=1: a + b
        functions_mapping['add_two_nums'] = add_two_nums
        assert parser.parse_data(
            '${add_two_nums(1)}', functions_mapping=functions_mapping) == 2
        assert parser.parse_data(
            '${add_two_nums(1,2)}', functions_mapping=functions_mapping) == 3
        assert parser.parse_data(
            '/api/${add_two_nums(1,2)}',
            functions_mapping=functions_mapping) == '/api/3'
        with pytest.raises(exceptions.FunctionNotFound):
            parser.parse_data('/api/${gen_md5(abc)}')

    def test_parse_data_testcase(self):
        variables = {
            'uid': '1000',
            'random': 'A2dEx',
            'authorization': 'a83de0ff8d2e896dbd8efb81ba14e17d',
            'data': {
                'name': 'user',
                'password': '123456'
            }
        }
        functions = {
            'add_two_nums': lambda a, b=1: a + b,
            'get_timestamp': lambda: int(time.time() * 1000)
        }
        testcase_template = {
            'url': 'http://127.0.0.1:5000/api/users/$uid/${add_two_nums(1,2)}',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'authorization': '$authorization',
                'random': '$random',
                'sum': '${add_two_nums(1,2)}'
            },
            'body': '$data'
        }
        parsed_testcase = parser.parse_data(testcase_template, variables,
                                            functions)
        assert parsed_testcase[
            'url'] == 'http://127.0.0.1:5000/api/users/1000/3'
        assert parsed_testcase['headers'][
            'authorization'] == 'a83de0ff8d2e896dbd8efb81ba14e17d'
        assert parsed_testcase['headers']['random'] == variables['random']
        assert parsed_testcase['body'] == variables['data']
        assert parsed_testcase['headers']['sum'] == 3

    def test_substitute_variables(self):
        content = {
            'request': {
                'url': '/api/users/$uid',
                'headers': {
                    'token': '$token'
                }
            }
        }
        variables_mapping = {'$uid': 1000}
        subsitituted_data = parser.substitute_variables(
            content, variables_mapping)
        assert subsitituted_data['request']['url'] == '/api/users/1000'
        assert subsitituted_data['request']['headers']['token'] == '$token'

    def test_parse_parameters_raw_list(self):
        parameters = [{
            'user_agent': ['ios/10.1', 'ios/10.2', 'ios/10.3']
        }, {
            'username-password': [('user1', '111111'), ('user2', '222222')]
        }]
        variables_mapping = {}
        functions_mapping = {}
        cartesian_product_parameters = parser.parse_parameters(
            parameters, variables_mapping, functions_mapping)
        assert len(cartesian_product_parameters) == 3 * 2
        assert cartesian_product_parameters[0] == {
            'user_agent': 'ios/10.1',
            'username': 'user1',
            'password': '111111'
        }

    def test_parse_parameters_parameterize(self):
        parameters = [{
            'app_version':
            '${parameterize(tests/data/app_version.csv)}'
        }, {
            'username-password':
            '${parameterize(tests/data/account.csv)}'
        }]
        variables_mapping = {}
        functions_mapping = {}

        cartesian_product_parameters = parser.parse_parameters(
            parameters, variables_mapping, functions_mapping)

        print(cartesian_product_parameters)
        assert len(cartesian_product_parameters) == 2 * 3
