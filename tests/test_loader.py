# !/usr/bin/python
# -*- coding: utf-8 -*-

import os
import pytest

from httprunner import exceptions, loader


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


class TestModuleLoader:
    def test_filter_module_functions(self):
        module_mapping = loader.load_python_module(loader)
        functions_dict = module_mapping['functions']
        assert 'load_python_module' in functions_dict
        assert 'is_py3' not in functions_dict
