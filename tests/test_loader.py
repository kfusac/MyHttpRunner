# !/usr/bin/python
# -*- coding: utf-8 -*-

import os
import pytest

from httprunner import exceptions, loader, validator


class TestFileLoader:
    def test_load_yaml_file_file_format_error(self):
        yaml_tmp_file = 'tests/data/tmp.yml'

        # create empty yaml file
        with open(yaml_tmp_file, 'w') as f:
            f.write('')

        with pytest.raises(exceptions.FileFormatError):
            loader.load_yaml_file(yaml_tmp_file)

        os.remove(yaml_tmp_file)

        # create invalid format yaml file
        with open(yaml_tmp_file, 'w') as f:
            f.write('abc')

        with pytest.raises(exceptions.FileFormatError):
            loader.load_yaml_file(yaml_tmp_file)

        os.remove(yaml_tmp_file)

    def test_load_json_file_file_format_error(self):
        json_tmp_file = 'tests/data/tmp.json'

        # create empty file
        with open(json_tmp_file, 'w') as f:
            f.write('')

        with pytest.raises(exceptions.FileFormatError):
            loader.load_json_file(json_tmp_file)

        os.remove(json_tmp_file)

        # create empty json file
        with open(json_tmp_file, 'w') as f:
            f.write('{}')

        with pytest.raises(exceptions.FileFormatError):
            loader.load_json_file(json_tmp_file)

        os.remove(json_tmp_file)

        # create invalid format json file
        with open(json_tmp_file, 'w') as f:
            f.write('abc')

        with pytest.raises(exceptions.FileFormatError):
            loader.load_json_file(json_tmp_file)

        os.remove(json_tmp_file)

    def test_load_testcases_bad_filepath(self):
        testcases_bad_file_path = os.path.join(os.getcwd(), 'tests', 'data',
                                               'demo')
        with pytest.raises(exceptions.FileNotFound):
            loader.load_file(testcases_bad_file_path)

    def test_load_json_testcases(self):
        testcases_file_path = os.path.join(os.getcwd(), 'tests', 'data',
                                           'demo_testset_hardcode.json')
        testcases = loader.load_file(testcases_file_path)
        assert len(testcases) == 3
        test = testcases[0]['test']
        assert 'name' in test
        assert 'request' in test
        assert 'url' in test['request']
        assert 'method' in test['request']

    def test_load_csv_file_one_parameter(self):
        csv_file_path = os.path.join(os.getcwd(), 'tests', 'data',
                                     'user_agent.csv')
        csv_content = loader.load_file(csv_file_path)
        assert csv_content == [{
            'user_agent': 'ios/10.1'
        }, {
            'user_agent': 'ios/10.2'
        }, {
            'user_agent': 'ios/10.3'
        }]

    def test_load_csv_file_multiple_parameters(self):
        csv_file_path = os.path.join(os.getcwd(), 'tests', 'data',
                                     'account.csv')
        csv_content = loader.load_csv_file(csv_file_path)
        assert csv_content == [{
            'username': 'test1',
            'password': '111111'
        }, {
            'username': 'test2',
            'password': '222222'
        }, {
            'username': 'test3',
            'password': '333333'
        }]

    def test_load_folder_files(self):
        folder = os.path.join(os.getcwd(), 'tests')
        file1 = os.path.join(os.getcwd(), 'tests', 'test_apiserver.py')
        file2 = os.path.join(os.getcwd(), 'tests', 'data', 'demo_binds.yml')

        files = loader.load_folder_files(folder, recursive=False)
        assert file2 not in files

        files = loader.load_folder_files(folder)
        assert file1 not in files
        assert file2 in files

        files = loader.load_folder_files(folder)
        api_file = os.path.join(os.getcwd(), 'tests', 'api', 'basic.yml')
        assert api_file in files

        files = loader.load_folder_files(
            'not existed_folder_path', recursive=False)
        assert files == []

        files = loader.load_folder_files(file2, recursive=False)
        assert files == []

    def test_locate_file(self):
        with pytest.raises(exceptions.FileNotFound):
            loader.locate_file(os.getcwd(), 'confcustom.py')

        with pytest.raises(exceptions.FileNotFound):
            loader.locate_file('', 'confcustom.py')

        start_path = os.path.join(os.getcwd(), 'tests')
        assert loader.locate_file(start_path, 'confcustom.py') == os.path.join(
            os.getcwd(), 'tests', 'confcustom.py')

        assert loader.locate_file('tests/', 'confcustom.py') == os.path.join(
            'tests', 'confcustom.py')
        assert loader.locate_file('tests', 'confcustom.py') == os.path.join(
            'tests', 'confcustom.py')
        assert loader.locate_file('tests/base.py',
                                  'confcustom.py') == os.path.join(
                                      'tests', 'confcustom.py')
        assert loader.locate_file('tests/data/account.csv',
                                  'confcustom.py') == os.path.join(
                                      'tests', 'confcustom.py')

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(os.getcwd(), 'tests', '.env')),
        reason='.env not exist')
    def test_load_dot_env_file(self):
        loader.project_working_directory = os.path.join(os.getcwd(), 'tests')
        env_variables_mapping = loader.load_env_file()
        assert 'PROJECT_KEY' in env_variables_mapping
        assert env_variables_mapping['UserName'] == 'testuser'
        assert os.environ['password'] == '123456'

    def test_load_env_path_not_exist(self):
        loader.project_working_directory = os.path.join(
            os.getcwd(), 'tests', 'data')
        loader.load_env_file()


class TestModuleLoader:
    def test_filter_module_functions(self):
        module_mapping = loader.load_python_module(loader)
        functions_dict = module_mapping['functions']
        assert 'load_python_module' in functions_dict
        assert 'is_py3' not in functions_dict

    def test_load_confcustom_module(self):
        loader.load_project_tests(os.path.join(os.getcwd(), 'httprunner'))
        imported_module_items = loader.project_mapping['confcustom']
        assert 'equals' in imported_module_items['functions']
        assert 'SECRET_KEY' not in imported_module_items['variables']
        assert 'alter_response' not in imported_module_items['functions']

        loader.load_project_tests(os.path.join(os.getcwd(), 'tests'))
        imported_module_items = loader.project_mapping['confcustom']
        assert imported_module_items['variables'][
            'SECRET_KEY'] == 'MyHttpRunner'
        assert 'hook_print' in imported_module_items['functions']
        is_status_code_200 = imported_module_items['functions'][
            'is_status_code_200']
        assert is_status_code_200(200)
        assert not is_status_code_200(300)

    def test_get_module_item_functions(self):
        from httprunner import utils
        module_mapping = loader.load_python_module(utils)

        get_uniform_comparator = loader.get_module_item(
            module_mapping, 'functions', 'get_uniform_comparator')
        assert validator.is_function(("get_uniform_comparator",
                                      get_uniform_comparator))
        assert get_uniform_comparator('==') == 'equals'

        with pytest.raises(exceptions.FunctionNotFound):
            loader.get_module_item(module_mapping, 'functions', 'gen_md4')

    def test_get_module_item_variables(self):
        from tests import confcustom
        module_mapping = loader.load_python_module(confcustom)

        SECRET_KEY = loader.get_module_item(module_mapping, 'variables',
                                            'SECRET_KEY')
        assert validator.is_variable(('SECRET_KEY', SECRET_KEY))
        assert SECRET_KEY == 'MyHttpRunner'

    def test_locate_confcustom_py(self):
        confcustom_path = loader.locate_confcustom_py(
            'tests/data/demo_testcase.yml')
        assert confcustom_path == os.path.join(os.getcwd(), 'tests',
                                               'confcustom.py')

        confcustom_path = loader.locate_confcustom_py('tests/base.py')
        assert confcustom_path == os.path.join(os.getcwd(), 'tests',
                                               'confcustom.py')

        confcustom_path = loader.locate_confcustom_py('httprunner/__init__py')
        assert confcustom_path is None


class TestSuiteLoader:
    @classmethod
    def setup_class(cls):
        loader.load_project_tests(os.path.join(os.getcwd(), 'tests'))

    def test_load_test_file_testcase(self):
        testcase = loader._load_test_file('tests/testcases/smoketest.yml')
        assert testcase['config']['name'] == 'smoketest'
        assert 'device_sn' in testcase['config']['variables'][0]
        assert len(testcase['teststeps']) == 8
        assert testcase['teststeps'][0]['name'] == "get token"

    def test_get_block_by_name(self):
        ref_call = "get_user($uid,$token)"
        block = loader._get_block_by_name(ref_call, "def-api")
        assert block['request']['url'] == '/api/users/$uid'
        assert block['function_meta']['func_name'] == 'get_user'
        assert block['function_meta']['args'] == ['$uid', '$token']

    def test_get_block_by_name_args_mismatch(self):
        ref_call = 'get_user($uid,$token,$var)'
        with pytest.raises(exceptions.ParamError):
            loader._get_block_by_name(ref_call, 'def-api')

    def test_override_block(self):
        def_block = loader._get_block_by_name(
            "get_token($user_agent,$device_sn,$os_platform,$app_version)",
            "def-api")
        test_block = {
            'name':
            'override block',
            'variables': [{
                'var': 123
            }],
            'request': {
                'url': '/api/get-token',
                'method': 'POST',
                'headers': {
                    'user_agent': '$user_agent',
                    'device_sn': '$device_sn',
                    'os_platform': '$os_platform',
                    'app_version': '$app_version'
                },
                'json': {
                    'sign':
                    '${get_sign($user_agent,$device_sn,$os_platform,$app_version)}'
                }
            },
            'validate': [{
                'eq': ['status_code', 201]
            }, {
                'len_eq': ['content.token', 32]
            }]
        }

        loader._extend_block(test_block, def_block)
        assert test_block['name'] == 'override block'
        assert {
            'check': 'status_code',
            'expect': 201,
            'comparator': 'eq'
        } in test_block['validate']
        assert {
            'check': 'content.token',
            'expect': 32,
            'comparator': 'len_eq'
        } in test_block['validate']

    def test_get_test_definition_api(self):
        api_def = loader._get_test_definition('get_headers', 'def-api')
        assert api_def['request']['url'] == '/headers'
        assert len(api_def['setup_hooks']) == 2
        assert len(api_def['teardown_hooks']) == 1

    def test_get_test_definition_suite(self):
        suite_def = loader._get_test_definition('create_and_check',
                                                'def-testcase')
        assert suite_def['config']['name'] == 'create user and check result.'
        with pytest.raises(exceptions.TestcaseNotFound):
            loader._get_test_definition('create_and_check_xxx', 'def-testcase')

    def test_merge_validator(self):
        def_validators = [{
            'eq': ['v1', 200]
        }, {
            'check': 's2',
            'expect': 16,
            'comparator': 'len_eq'
        }]
        current_validators = [{
            'check': 'v1',
            'expect': 201
        }, {
            'len_eq': ['s3', 12]
        }]

        merged_validators = loader._merge_validator(def_validators,
                                                    current_validators)
        assert {
            'check': 'v1',
            'expect': 201,
            'comparator': 'eq'
        } in merged_validators
        assert {
            'check': 's2',
            'expect': 16,
            'comparator': 'len_eq'
        } in merged_validators
        assert {
            'check': 's3',
            'expect': 12,
            'comparator': 'len_eq'
        } in merged_validators

    def test_merge_validator_with_dict(self):
        def_validators = [{'eq': ['a', {'v1': 1}]}, {'eq': [{'b': 1}, 201]}]
        current_validators = [{'len_eq': ['s3', 12]}, {'eq': [{'b': 1}, 201]}]
        merged_validators = loader._merge_validator(def_validators,
                                                    current_validators)
        assert len(merged_validators) == 3
        assert {
            'check': {
                'b': 1
            },
            'expect': 201,
            'comparator': 'eq'
        } in merged_validators
        assert {
            'check': {
                'b': 1
            },
            'expect': 200,
            'comparator': 'eq'
        } not in merged_validators

    def test_merge_extractor(self):
        api_extrators = [{'var1': 'val1'}, {'var2': 'val2'}]
        current_extrators = [{'var1': 'val111'}, {'var3': 'val3'}]

        merged_extrators = loader._merge_extractor(api_extrators,
                                                   current_extrators)
        assert {'var1': 'val111'} in merged_extrators
        assert {'var2': 'val2'} in merged_extrators
        assert {'var3': 'val3'} in merged_extrators

    def test_load_testcases_by_path_files(self):
        testsets_list = []

        # absolute file path
        path = os.path.join(os.getcwd(),
                            'tests/data/demo_testset_hardcode.json')
        testset_list = loader.load_testcases(path)
        assert len(testset_list) == 1
        assert len(testset_list[0]['teststeps']) == 3
        testsets_list.extend(testset_list)

        # relative file path
        path = 'tests/data/demo_testset_hardcode.yml'
        testset_list = loader.load_testcases(path)
        assert len(testset_list) == 1
        assert len(testset_list[0]['teststeps']) == 3
        testsets_list.extend(testset_list)

        # list/set container with file(s)
        path = [
            os.path.join(os.getcwd(), 'tests/data/demo_testset_hardcode.json'),
            'tests/data/demo_testset_hardcode.yml'
        ]
        testset_list = loader.load_testcases(path)
        assert len(testset_list) == 2
        assert len(testset_list[0]['teststeps']) == 3
        assert len(testset_list[1]['teststeps']) == 3
        testsets_list.extend(testset_list)
        assert len(testsets_list) == 4

        for testset in testsets_list:
            for test in testset['teststeps']:
                assert 'name' in test
                assert 'request' in test
                assert 'url' in test['request']
                assert 'method' in test['request']

    def test_load_testcases_by_path_folder(self):
        # absolute folder path
        path = os.path.join(os.getcwd(), 'tests/data')
        testset_list_1 = loader.load_testcases(path)
        assert len(testset_list_1) > 1

        # relative folder path
        path = 'tests/data/'
        testset_list_2 = loader.load_testcases(path)
        assert len(testset_list_1) == len(testset_list_2)

        # list/set container with folder(s)
        path = [os.path.join(os.getcwd(), 'tests/data'), 'tests/data/']
        testset_list_3 = loader.load_testcases(path)
        assert len(testset_list_3) == 2 * len(testset_list_1)

    def test_load_testcases_by_path_not_exist(self):
        # absolute folder path
        path = os.path.join(os.getcwd(), 'tests/data_not_exist')
        with pytest.raises(exceptions.FileNotFound):
            loader.load_testcases(path)

        # relative folder path
        path = 'tests/data_not_exist'
        with pytest.raises(exceptions.FileNotFound):
            loader.load_testcases(path)

        # list/set container with folder(s)
        path = [
            os.path.join(os.getcwd(), 'tests/data_not_exist'),
            'tests/data_not_exist'
        ]
        with pytest.raises(exceptions.FileNotFound):
            loader.load_testcases(path)

    def test_load_testcases_by_path_layered(self):
        path = os.path.join(os.getcwd(), 'tests/data/demo_testset_layer.yml')
        testsets_list = loader.load_testcases(path)
        assert 'variables' in testsets_list[0]['config']
        assert 'request' in testsets_list[0]['config']
        assert 'request' in testsets_list[0]['teststeps'][0]
        assert 'url' in testsets_list[0]['teststeps'][0]['request']
        assert 'validate' in testsets_list[0]['teststeps'][0]

    def test_load_folder_content(self):
        path = os.path.join(os.getcwd(), 'tests', 'api')
        items_mapping = loader.load_folder_content(path)
        file_path = os.path.join(os.getcwd(), 'tests', 'api', 'basic.yml')
        assert file_path in items_mapping
        assert isinstance(items_mapping[file_path], list)

    def test_laod_api_folder(self):
        path = os.path.join(os.getcwd(), 'tests', 'api')
        api_definition_mapping = loader.load_api_folder(path)
        assert 'get_token' in api_definition_mapping
        assert 'request' in api_definition_mapping['get_token']
        assert 'function_meta' in api_definition_mapping['get_token']

    def test_load_testcases_folder(self):
        path = os.path.join(os.getcwd(), 'tests', 'suite')
        testcases_definition_mapping = loader.load_test_folder(path)

        assert 'setup_and_reset' in testcases_definition_mapping
        assert 'create_and_check' in testcases_definition_mapping
        assert testcases_definition_mapping['setup_and_reset']['config'][
            'name'] == 'setup and reset all.'
        assert testcases_definition_mapping['setup_and_reset'][
            'function_meta']['func_name'] == 'setup_and_reset'

    def test_load_testsuites_folder(self):
        path = os.path.join(os.getcwd(), 'tests', 'testcases')
        testsuites_definition_mapping = loader.load_test_folder(path)

        testsuite_path = os.path.join(os.getcwd(), 'tests', 'testcases',
                                      'smoketest.yml')
        assert testsuite_path in testsuites_definition_mapping
        assert testsuites_definition_mapping[testsuite_path]['config'][
            'name'] == 'smoketest'

    def test_load_project_tests(self):
        loader.load_project_tests(os.path.join(os.getcwd(), 'tests'))
        project_mapping = loader.project_mapping
        assert project_mapping['confcustom']['variables'][
            'SECRET_KEY'] == 'MyHttpRunner'
        assert 'get_token' in project_mapping['def-api']
        assert 'setup_and_reset' in project_mapping['def-testcase']
        if not os.path.exists(os.path.join(os.getcwd(), 'tests', '.env')):
            pytest.skip('.env not exists')
        assert project_mapping['env']['PROJECT_KEY'] == 'ABCDEFGH'
