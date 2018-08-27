# !/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import csv
import yaml
import sys
import importlib

from httprunner import logger, exceptions, validator

sys.path.insert(0, os.getcwd())

project_mapping = {
    'confcustom': {
        'variables': {},
        'functions': {}
    },
    'def-api': {},
    'def-testcase': {}
}

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
