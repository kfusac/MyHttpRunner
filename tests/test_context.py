# !/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time

import requests

from httprunner import exceptions, context, loader
from tests.base import TestApiServerBase


class TestContext(TestApiServerBase):
    def setup_method(self):
        loader.load_project_tests(os.path.join(os.getcwd(), 'tests'))
        self.confcustom_module = loader.project_mapping['confcustom']

        self.context = context.Context(self.confcustom_module['variables'],
                                       self.confcustom_module['functions'])
        testcase_file_path = os.path.join(os.getcwd(),
                                          'tests/data/demo_binds.yml')
        self.testcases = loader.load_file(testcase_file_path)

    def test_init_context_functions(self):
        context_functions = self.context.TESTCASE_SHARED_FUNCTIONS_MAPPING
        assert 'gen_md5' in context_functions
        assert 'equals' in context_functions

    def test_init_context_variables(self):
        assert self.context.teststep_variables_mapping[
            'SECRET_KEY'] == 'MyHttpRunner'
        assert self.context.testcase_runtime_variables_mapping[
            'SECRET_KEY'] == 'MyHttpRunner'

    def test_update_context_testcase_level(self):
        variables = [{
            'TOKEN': 'test'
        }, {
            'data': '{"name":"user","password":"123456}'
        }]
        self.context.update_context_variables(variables, 'testcase')
        assert self.context.teststep_variables_mapping['TOKEN'] == 'test'
        assert self.context.testcase_runtime_variables_mapping[
            'TOKEN'] == 'test'

    def test_update_context_teststep_level(self):
        variables = [{
            'TOKEN': 'test'
        }, {
            'data': '{"name":"user","password":"123456}'
        }]
        self.context.update_context_variables(variables, 'teststep')
        assert self.context.teststep_variables_mapping['TOKEN'] == 'test'
        assert 'TOKEN' not in self.context.testcase_runtime_variables_mapping

    def test_eval_content_functions(self):
        content = "${sleep_N_secs(1)}"
        start_time = time.time()
        self.context.eval_content(content)
        elasped_time = time.time() - start_time
        assert elasped_time >= 1

    def test_eval_content_variables(self):
        content = 'abc$SECRET_KEY'
        assert self.context.eval_content(content) == 'abcMyHttpRunner'

        content = 'abc$SECRET_KEYdef'
        assert self.context.eval_content(content) == 'abcMyHttpRunnerdef'

    def test_update_testcase_runtime_variables_mapping(self):
        variables = {'abc': 123}
        self.context.update_testcase_runtime_variables_mapping(variables)
        assert self.context.testcase_runtime_variables_mapping['abc'] == 123
        assert self.context.teststep_variables_mapping['abc'] == 123

    def test_update_teststep_variables_mapping(self):
        self.context.update_teststep_variables_mapping('abc', 123)
        assert self.context.teststep_variables_mapping['abc'] == 123
        assert 'abc' not in self.context.testcase_runtime_variables_mapping

    def test_get_parsed_request(self):
        variables = [{
            'TOKEN': 'confcustom'
        }, {
            'random': '${gen_random_string(5)}'
        }, {
            'data': {
                'name': 'user',
                'password': '123456'
            }
        }, {
            'authorization': '${gen_md5($TOKEN,$data,$random)}'
        }]
        self.context.update_context_variables(variables, 'teststep')

        request = {
            'url': 'http://127.0.0.1:5000/api/users/1000',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'authorization': '$authorization',
                'random': '$random',
                'secret_key': '$SECRET_KEY'
            },
            'data': '$data'
        }
        parsed_request = self.context.get_parsed_request(
            request, level='teststep')
        assert 'authorization' in parsed_request['headers']
        assert len(parsed_request['headers']['authorization']) == 32
        assert 'random' in parsed_request['headers']
        assert len(parsed_request['headers']['random']) == 5
        assert 'data' in parsed_request
        assert parsed_request['data'] == variables[2]['data']
        assert parsed_request['headers']['secret_key'] == 'MyHttpRunner'

    def test_do_validation(self):
        self.context._do_validation({
            'check': 'check',
            'check_value': 1,
            'expect': 1,
            'comparator': 'eq'
        })
        self.context._do_validation({
            'check': 'check',
            'check_value': 'abc',
            'expect': 'abc',
            'comparator': '=='
        })
        self.context._do_validation({
            'check': 'status_code',
            'check_value': 201,
            'expect': 3,
            'comparator': 'sum_status_code'
        })
