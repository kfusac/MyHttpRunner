# !/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import csv
import yaml
import sys
import importlib
import collections

from httprunner import logger, exceptions, validator, utils, parser

sys.path.insert(0, os.getcwd())

project_mapping = {
    'confcustom': {
        'variables': {},
        'functions': {}
    },
    'env': {},
    'def-api': {},
    'def-testcase': {}
}

testcases_cache_mapping = {}
project_working_directory = os.getcwd()

###############################################################################
#   file loader
###############################################################################


def load_yaml_file(yaml_file_path):
    '''
    load yaml file and check file content format
    '''

    with open(yaml_file_path, 'r', encoding='utf-8') as stream:
        yaml_content = yaml.load(stream)
        _check_format(yaml_file_path, yaml_content)
        if not isinstance(yaml_content, (list, dict)):
            err_msg = f'YAML file format error: {yaml_file_path}'
            logger.log_error(err_msg)
            raise exceptions.FileFormatError(err_msg)
        return yaml_content


def load_json_file(json_file_path):
    '''
    load json file and check file content format
    '''

    with open(json_file_path, 'r', encoding='utf-8') as data_file:
        try:
            json_content = json.load(data_file)
        except exceptions.JSONDecodeError:
            err_msg = f'JSONDecodeError: JSON file format error: {json_file_path}'
            logger.log_error(err_msg)
            raise exceptions.FileFormatError(err_msg)
        _check_format(json_file_path, json_content)
        return json_content


def load_csv_file(csv_file_path):
    '''
    load csv file and check file content format
    Args:
        csv_file_path (str): csv file path
        e.g. csv file content:
            username,password
            test1,111111
            test2,222222
            test3,333333
    Returns:
        list of parameter, each parameter is in dict format
        e.g.
        [
            {'username':'test1','password':'111111'},
            {'username':'test2','password':'222222'},
            {'username':'test3','password':'333333'}
        ]
    '''
    csv_content_list = []

    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            csv_content_list.append(row)

    return csv_content_list


def load_file(file_path):
    if not os.path.isfile(file_path):
        raise exceptions.FileNotFound(f'{file_path} does not exist.')
    file_suffix = os.path.splitext(file_path)[1].lower()
    if file_suffix == '.json':
        return load_json_file(file_path)
    elif file_suffix in ['.yaml', '.yml']:
        return load_json_file(file_path)
    elif file_suffix == '.csv':
        return load_csv_file(file_path)
    else:
        err_msg = f'Unsupported file format: {file_path}'
        logger.log_error(err_msg)
        return []


def load_folder_files(folder_path, recursive=True):
    '''
    load folder path, return all files endswith yml/yaml/json in list.
    Args:
        folder_path (str): specified folder path to load
        recursive (bool): load files recursively if True
    Returns:
        list: files endswith yml/yaml/json
    '''

    if isinstance(folder_path, (list, set)):
        files = []
        for path in set(folder_path):
            files.extend(load_folder_files(path, recursive))

    if not os.path.exists(folder_path):
        return []

    files_list = []

    for dirpath, dirnames, filenames in os.walk(folder_path):
        filenames_list = []

        for filename in filenames:
            if not filename.endswith(('.yml', '.yaml', '.json')):
                continue
            filenames_list.append(filename)

        for filename in filenames_list:
            file_path = os.path.join(dirpath, filename)
            files_list.append(file_path)

        if not recursive:
            break

    return files_list


def locate_file(start_path, file_name):
    '''
    locate filename and return file path.
    searching will be recursive upward until current working directory.
    Args:
        start_path (str): start locating path, maybe file path or directory path.
        file_name (str): specified file name.
    Returns:
        str: located file path. None if file not found.
    Raises:
        exceptions.FileNotFound: If failed to locate file.
    '''
    start_path = start_path.rstrip('/').rstrip('\\')
    if os.path.isfile(start_path):
        start_dir_path = os.path.dirname(start_path)
    elif os.path.isdir(start_path):
        start_dir_path = start_path
    else:
        raise exceptions.FileNotFound(f'invalid path:{start_path}')

    file_path = os.path.join(start_dir_path, file_name)
    if os.path.isfile(file_path):
        return file_path

    # current working directory
    if os.path.abspath(start_dir_path) in [
            os.getcwd(), os.path.abspath(os.sep)
    ]:
        raise exceptions.FileNotFound(f'{file_name} not found in {start_path}')

    # locate recursive upward
    return locate_file(os.path.dirname(start_dir_path), file_name)


def load_env_file():
    '''
    load .env file, .env file should be located in project working directory.
    Returns:
        dict: enviroment variables mapping
            {
                'username':'testuser',
                'password':'123456',
                'PROJECT_KEY':'ABCDEFGH'
            }
    Raises:
        exceptions.FileFormatError: If env file format is invalid.
    '''

    path = os.path.join(project_working_directory, '.env')
    if not os.path.isfile(path):
        logger.log_debug(
            f'.env file not exist in: {project_working_directory}')
        return {}

    logger.log_info(f'Loading enviroment variables from {path}')
    env_variables_mapping = {}
    with open(path, 'r', encoding='utf-8') as fp:
        for line in fp:
            if '=' in line:
                variable, value = line.split('=')
            elif ':' in line:
                variable, value = line.split(':')
            else:
                raise exceptions.FileFormatError('.env format error')

            env_variables_mapping[variable.strip()] = value.strip()

    project_mapping['env'] = env_variables_mapping
    utils.set_os_environ(env_variables_mapping)

    return env_variables_mapping


def _check_format(file_path, content):
    '''
    check testcase format if valid
    '''

    if not content:  # empty file
        err_msg = f'Testcase file content is empty: {file_path}'
        logger.log_error(err_msg)
        raise exceptions.FileFormatError(err_msg)


###############################################################################
#   confcustom.py loader
###############################################################################


def load_python_module(module):
    '''
    load python module.
    Args:
        module: python module custom or build-in module
    Returns:
        dict: variables and functions mapping for specified python module
            {
                'variables':{},
                'functions':{}
            }
    '''

    confcustom_module = {'variables': {}, 'functions': {}}

    for name, item in vars(module).items():
        if validator.is_function((name, item)):
            confcustom_module['functions'][name] = item
        elif validator.is_variable((name, item)):
            confcustom_module['variables'][name] = item
        else:
            pass

    return confcustom_module


def load_builtin_module():
    '''
    load built_in module
    '''

    from httprunner import built_in

    built_in_module = load_python_module(built_in)
    project_mapping['confcustom']['variables'].update(
        built_in_module['variables'])
    project_mapping['confcustom']['functions'].update(
        built_in_module['functions'])


def load_confcustom_module():
    '''
    load project confcustom.py mofule and merge with builtin module.
    confcustom.py should be located in project working directory.
    variables and functions mapping for confcustom.py
        {
            'variables':{},
            'functions':{}
        }
    '''

    imported_module = importlib.import_module('confcustom')
    confcustom_module = load_python_module(imported_module)
    project_mapping['confcustom']['variables'].update(
        confcustom_module['variables'])
    project_mapping['confcustom']['functions'].update(
        confcustom_module['functions'])


def get_module_item(module_mapping, item_type, item_name):
    '''
    get excepted function or variable from module mapping.
    Args:
        module_mapping (dict): module mapping with variables and functions.
            {
                'variables':{},
                'functions':{}
            }
        item_type (str): 'functions' or 'variables'
        item_name (str): specified function name or variable name
    Returns:
        object: specified variable or function object.
    Raises:
        exceptions.FunctionNotFound: If specified function not found in module mapping.
        exceptions.VariableNotFound: If specified variable not found in module mapping.
    '''
    try:
        return module_mapping[item_type][item_name]
    except KeyError:
        err_msg = f'{item_name} not found in confcustom.py module!'
        logger.log_error(err_msg)
        if item_type == 'functions':
            raise exceptions.FunctionNotFound(err_msg)
        else:
            raise exceptions.VariableNotFound(err_msg)


###############################################################################
#   testcase loader
###############################################################################


def _load_test_file(file_path):
    '''
    load testcase file or testsuite file
    Args:
        file_path (str): absolute valid file path. file should be in the following format:
            e.g.
            [
                {
                    "config":{
                        "name":"",
                        "def":"suite_order()",
                        "request":{}
                    }
                },
                {
                    "test":{
                        "name":"add product to cart",
                        "api":"api_add_cart()",
                        "validate":[]
                    }
                },
                {
                    "test":{
                        "name":"add product to cart",
                        "suite":"create_and_check()",
                        validate":[]
                    }
                },
                {
                    "test":{
                        "name":"checkout cart",
                        "request":{},
                        "validate":[]
                    }
                }
            ]
    Returns:
        dict: testcase dict
            {
                "config":{},
                "teststeps":[teststep1,teststep2]
            }
    '''
    testcase = {"config": {}, "teststeps": []}

    for item in load_file(file_path):
        if not isinstance(item, dict) or len(item) != 1:
            raise exceptions.FileFormatError(
                f'Testcase format error: {file_path}')

        key, test_block = item.popitem()
        if not isinstance(test_block, dict):
            raise exceptions.FileFormatError(
                f'Testcase format error: {file_path}')

        if key == "config":
            testcase["config"].update(test_block)
        elif key == 'test':

            def extend_api_definition(block):
                ref_call = block("api")
                def_block = _get_block_by_name(ref_call, 'def-api')
                _extend_block(block, def_block)

            if 'api' in test_block:
                extend_api_definition(test_block)
                testcase['teststeps'].append(test_block)
            elif 'suite' in test_block:
                ref_call = test_block['suite']
                block = _get_block_by_name(ref_call, 'def-testcase')
                for teststep in block['teststeps']:
                    if 'api' in teststep:
                        extend_api_definition(teststep)
                    testcase['teststeps'].append(teststep)
            else:
                testcase['teststeps'].append(test_block)
        else:
            logger.log_warning(
                f'unexpected block key: {key}. block key should only be "config" or "test".'
            )

    return testcase


def _get_block_by_name(ref_call, ref_type):
    '''
    get test content by reference name.
    Args:
        ref_call (str): call function.
            e.g. api_v1_Account_Login_POST($UserName,$Password)
        ref_type (enum): "def-api" or "def-testcase"
    Returns:
        dict: api/testcase definition
    Raises:
        exceptions.ParamsError: call args number is not equal to defined args number
    '''

    function_meta = parser.parse_function(ref_call)
    func_name = function_meta['func_name']
    call_args = function_meta['args']
    block = _get_test_definition(func_name, ref_type)
    def_args = block.get('function_meta', {}).get('args', [])

    if len(call_args) != len(def_args):
        err_msg = f'{func_name}: call args number is not equal to defined args number!\n'
        err_msg += f'defined args: {def_args}\n'
        err_msg += f'refererce args: {call_args}'
        logger.log_error(err_msg)
        raise exceptions.ParamError(err_msg)

    args_mapping = {}
    for index, item in enumerate(def_args):
        if call_args[index] == item:
            continue
        args_mapping[item] = call_args[index]

    if args_mapping:
        block = parser.substitute_variables(block, args_mapping)

    return block


def _get_test_definition(name, ref_type):
    '''
    get expected api or testcase.
    Args:
        name (str): specified api or testcase name
        ref_type (enum): "def-api" or "testcase"
    Returns:
        dict: expected api/testcase info if found.
    Raises:
        exceptions.ApiNotFound: api not found
        exceptions.TestcaseNotFound: testcase not found
    '''
    block = project_mapping.get(ref_type, {}).get(name)

    if not block:
        err_msg = f'{name} not found!'
        if ref_type == 'def-api':
            logger.log_error(err_msg)
            raise exceptions.ApiNotFound(err_msg)
        else:
            logger.log_error(err_msg)
            raise exceptions.TestcaseNotFound(err_msg)

    return block


def _extend_block(ref_block, def_block):
    '''
    extend ref_block with def_block
    Args:
        def_block (dict): api definition dict.
        ref_block (dict): reference block
    Returns:
        dict: extended reference block.
    Examples:
        >>> def_block = {
                "name":"get token 1",
                "request": {...},
                "validate": [{"eq":['status_code',200]}]
            }
        >>> ref_block = {
                "name":"get token 2",
                "extract": [{"token":"content.token'}],
                "validate": [{'eq': ['status_code', 201]},{'len_eq': ['content.token',16]}]
            }
        >>> _extend_block(def_block, ref_block)
            {
                "name":"get token 2",
                "request":{...},
                "extract": [{"token":"content.token'}],
                "validate": [{'eq': ['status_code', 201]},{'len_eq': ['content.token',16]}]
            }
    '''
    def_validators = def_block.get('validate') or def_block.get(
        'validators', [])
    ref_validators = ref_block.get('validate') or ref_block.get(
        'validators', [])

    def_extrators = def_block.get('extract') or def_block.get(
        'extractors') or def_block.get('extract_binds', [])
    ref_extrators = ref_block.get('extract') or ref_block.get(
        'extractors') or ref_block.get('extract_binds', [])

    ref_block.update(def_block)
    ref_block['validate'] = _merge_validator(def_validators, ref_validators)

    ref_block['extract'] = _merge_extractor(def_extrators, ref_extrators)


def _convert_validators_to_mapping(validators):
    '''
    convert validators list to mapping.
    Args:
        validators (list): validators in list
    Returns:
        dict: validators mapping, use (check, comparator) as key.
    Examples:
        >>> validators = [
                {'check':'v1','expect':201,'comparator':'eq'},
                {'check':{'b':1},'expect':201,'comparator':'eq'}
            ]
        >>> _convert_validators_to_mapping(validators)
            {
                ('v1','eq'):{'check':'v1','expect':201,'comparator':'eq},
                ('{'b':1}','eq'):{'check':{'b':1'},'expect':201,'comparator':'eq'}
            }
    '''
    validators_mapping = {}
    for validate in validators:
        validate = parser.parse_validator(validate)

        if not isinstance(validate['check'], collections.Hashable):
            check = json.dumps(validate['check'])
        else:
            check = validate['check']

        key = (check, validate['comparator'])
        validators_mapping[key] = validate

    return validators_mapping


def _merge_validator(def_validators, ref_validators):
    '''
    merge def_validators with ref_validators.
    Args:
        def_validators (list)
        ref_validators (list)
    Returns:
        list: merged validators
    Examples:
        >>> def_validators = [{'eq':['v1',200]},{'check':'s2','expect':16,'comparator':'len_eq'}]
        >>> ref_validators = [{'check':'v1','expect':201,'comparator':'eq'},{'len_eq':['s3',12]}]
        >>> _merge_validator(def_validators, ref_validators)
            [
                {'check':'v1','expect':201,'comparator':'eq'},
                {'check':'s2','expect':16,'comparator':'len_eq'},
                {'check':'s3','expect':12,'comparator':'len_eq'},
            ]
    '''

    if not def_validators:
        return ref_validators
    elif not ref_validators:
        return def_validators
    else:
        def_validators_mapping = _convert_validators_to_mapping(def_validators)
        ref_validators_mapping = _convert_validators_to_mapping(ref_validators)

        def_validators_mapping.update(ref_validators_mapping)
        return list(def_validators_mapping.values())


def _merge_extractor(def_extractors, ref_extractors):
    '''
    merge def_extractors with ref_extractors
    Args:
        def_extractors (lsit): [{'var1':'val1'},{'var2':'val2'}]
        ref_extractors (list): [{'var1':'val111'},{'var3':'val3'}]
    Returns:
        list: merged extractors
    Examples:
        >>> def_extractors = [{'var1':'val1'},{'var2':'val2'}]
        >>> ref_extractors = [{'var1':'val111'},{'var3':'val3'}]
        >>> _merge_extractor(def_extractors,ref_extractors)
            [
                {'var1':'val111'},
                {'var2':'val2'},
                {'var3':'val3'}
            ]
    '''
    if not def_extractors:
        return ref_extractors
    elif not ref_extractors:
        return def_extractors
    else:
        extractor_dict = collections.OrderedDict()
        for api_extractor in def_extractors:
            if len(api_extractor) != 1:
                logger.log_warning(f'incorrect extractor: {api_extractor}')
                continue

            var_name = list(api_extractor.keys())[0]
            extractor_dict[var_name] = api_extractor[var_name]

        for test_extractor in ref_extractors:
            if len(test_extractor) != 1:
                logger.log_warning(f'incorrect extractor: {test_extractor}')
                continue

            var_name = list(test_extractor.keys())[0]
            extractor_dict[var_name] = test_extractor[var_name]

        extractor_list = []
        for key, value in extractor_dict.items():
            extractor_list.append({key: value})

        return extractor_list


def load_folder_content(folder_path):
    '''
    load api/testcases/testsuits files folder.
    Args:
        folder_path (str): api/testcase/testsuites files folder.
    Returns:
        dict: api definition mapping.
            {
                "tests/api/basic.yml':[
                    {'api':{'def':'api_login','request':{},'validate':[]}},
                    {'api':{'def':'api_logout','request':{},'validate':[]}},
                ]
            }
    '''

    items_mapping = {}

    for file_path in load_folder_files(folder_path):
        items_mapping[file_path] = load_file(file_path)

    return items_mapping


def load_api_folder(api_folder_path):
    '''
    load api definitions from api folder.
    Args:
        api_folder_path (str): api files folder.
            {
                'api':{
                    'def':'api_login',
                    'request':{},
                    'validate':[]
                }
            },
            {
                'api':{
                    'def':'api_logout',
                    'request':{},
                    'validate':[]
                }
            }
    Returns:
        dict: api definition mapping.
            {
                'api_login':{
                    'function_mata':{'func_name':'api_login','args':[],'kwargs':{}},
                    'request':{}
                },
                'api_logout':{
                    'function_mata':{'func_name':'api_logout','args':[],'kwargs':{}},
                    'request':{}
                }
            }
    '''
    api_definition_mapping = {}

    api_items_mapping = load_folder_content(api_folder_path)

    for api_file_path, api_items in api_items_mapping.items():
        for api_item in api_items:
            key, api_dict = api_item.popitem()

            api_def = api_dict.pop('def')
            function_meta = parser.parse_function(api_def)
            func_name = function_meta['func_name']

            if func_name in api_definition_mapping:
                logger.log_warning(f'API definition duplicated: {func_name}')

            api_dict['function_meta'] = function_meta
            api_definition_mapping[func_name] = api_dict

    project_mapping['def-api'] = api_definition_mapping
    return api_definition_mapping


def load_test_folder(test_folder_path):
    '''
    load testcases definition from folder.
    Args:
        test_folder_path (str): testcases files folder.
            testcase file should in the following format:
            [
                {
                    "config":{
                        "def":"create_and_check",
                        "request":{},
                        "validate":[]
                    }
                },
                {
                    "test":{
                        "api":"get_user",
                        "validate":[]
                    }
                }
            ]
    Returns:
        dict: testcases definition mapping.
            {
                "create_and_check":[
                    {"config":{}},
                    {"test":{}},
                    {"test":{}}
                ],
                "tests/testcases/create_and_get.yml":[
                    {"config":{}},
                    {"test":{}},
                    {"test":{}}
                ]
            }
    '''
    test_definition_mapping = {}

    test_items_mapping = load_folder_content(test_folder_path)

    for test_file_path, items in test_items_mapping.items():
        testcase = {"config": {}, "teststeps": []}
        for item in items:
            key, block = item.popitem()

            if key == 'config':
                testcase['config'].update(block)

                if "def" not in block:
                    test_definition_mapping[test_file_path] = testcase
                    continue

                testcase_def = block['def']
                function_meta = parser.parse_function(testcase_def)
                func_name = function_meta['func_name']

                if func_name in test_definition_mapping:
                    logger.log_warning(
                        f'testcase definition duplicated: {func_name}')

                testcase['function_meta'] = function_meta
                test_definition_mapping[func_name] = testcase
            else:
                testcase['teststeps'].append(block)

    project_mapping['def-testcase'] = test_definition_mapping
    return test_definition_mapping


def reset_loader():
    '''
    reset project mapping.
    '''
    global project_working_directory
    project_working_directory = os.getcwd()

    project_mapping['confcustom'] = {'variables': {}, 'functions': {}}
    project_mapping['env'] = {}
    project_mapping['def-api'] = {}
    project_mapping['def-testcase'] = {}
    testcases_cache_mapping.clear()


def locate_confcustom_py(start_path):
    '''
    locate confcustom.py file.
    Args:
        start_path (str): start locating path, maybe testcase file path or directory path.
    Returns:
        str: confcustom.py path
    '''
    try:
        confcustom_path = locate_file(start_path, 'confcustom.py')
        return os.path.abspath(confcustom_path)
    except exceptions.FileNotFound:
        return None


def load_project_tests(test_path):
    '''
    load api, testcases, .env, builtin module and confcustom.py
    Args:
        test_path (str): test file/folder path, locate pwd from this path.
    '''
    global project_working_directory

    reset_loader()
    load_builtin_module()

    confcustom_path = locate_confcustom_py(test_path)
    if confcustom_path:
        # The folder contains debugtalk.py will be treated as PWD.
        # add PWD to sys.path
        project_working_directory = os.path.dirname(confcustom_path)

        # load confcustom.py
        sys.path.index(0, project_working_directory)
        load_confcustom_module()
    else:
        # debugtalk.py not found, use os.getcwd() as PWD.
        project_working_directory = os.getcwd()

    load_env_file()
    load_api_folder(os.path.join(project_working_directory, 'api'))
    load_test_folder(os.path.join(project_working_directory, 'suite'))


def load_testcases(path):
    '''
    load testcases from file path, extend and merge with api/testcase definitions.
    Args:
        path (str/list/set): testcase file/folder path.
            path could be in several types:
                - absolute/relative file path
                - absolute/relative folder path
                - list/set container with file(s) and/or folder(s)
    Returns:
        list: testcases list, each testcase is corresponding to a file
        [
            testcase_dict_1,
            testcase_dict_2
        ]
    '''
    if isinstance(path, (list, set)):
        testcases_list = []

        for file_path in set(path):
            testcases = load_testcases(file_path)
            if not testcases:
                continue
            testcases_list.extend(testcases)

        return testcases_list

    if not os.path.isabs(path):
        path = os.path.join(project_working_directory, path)

    if path in testcases_cache_mapping:
        return testcases_cache_mapping[path]

    if os.path.isdir(path):
        load_project_tests(path)
        files_list = load_folder_files(path)
        testcases_list = load_testcases(files_list)
    elif os.path.isfile(path):
        try:
            load_project_tests(path)
            testcase = _load_test_file(path)
            if testcase['teststeps']:
                testcases_list = [testcase]
            else:
                testcases_list = []
        except exceptions.FileFormatError:
            testcases_list = []
    else:
        err_msg = f'path not exists: {path}'
        logger.log_error(err_msg)
        raise exceptions.FileNotFound(err_msg)

    testcases_cache_mapping[path] = testcases_list
    return testcases_list
