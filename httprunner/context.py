# !/usr/bin/python
# -*- coding: utf-8 -*-
import copy
from collections import OrderedDict

from httprunner import exceptions, logger, parser, utils


class Context:
    '''
    Manages context functions and variables.
    context has two levels, testcase and teststep.
    '''

    def __init__(self, variables=None, functions=None):
        # testcase level context
        self.TESTCASE_SHARED_VARIABLES_MAPPINGS = variables or OrderedDict()
        self.TESTCASE_SHARED_FUNCTIONS_MAPPING = functions or OrderedDict()

        # testcase level request
        self.TESTCASE_SHARED_REQUSET_MAPPING = {}

        self.evaluated_validators = []
        self.init_context_variables(level='testcase')

    def init_context_variables(self, level='textcase'):
        '''
        initialize testcase/teststep context
        Args:
            level (enum): 'testcase' or 'teststep'
        '''

        if level == 'testcase':
            self.testcase_runtime_variables_mapping = copy.deepcopy(
                self.TESTCASE_SHARED_VARIABLES_MAPPINGS)

        self.teststep_variables_mapping = copy.deepcopy(
            self.testcase_runtime_variables_mapping)

    def update_context_variables(self, variables, level):
        '''
        update context variables, with level specified.
        Args:
            variables (list/OrderedDict): testcase config block or teststep block
                [
                    {'TOKEN':'confcustom'},
                    {'random':'${gen_random_string(5)}'},
                    {'json':{'name':'user','password':'123456'}},
                    {'md5':'${gen_md5($TOKEN,$json,$random)}'}
                ]
                OrderedDict({
                    'TOKEN':'confcustom',
                    'random':'${gen_random_string(5)}',
                    'json':{'name':'user','password':'123456'},
                    'md5':'${gen_md5($TOKEN,$json,$random)}'
                })
            level (enum): 'testcase' or 'teststep'
        '''

        if isinstance(variables, list):
            variables = utils.convert_mappinglist_to_OrderedDict(variables)

        for variable_name, variable_value in variables.items():
            variable_evel_value = self.eval_content(variable_value)

            if level == 'testcase':
                self.testcase_runtime_variables_mapping[
                    variable_name] = variable_evel_value

            self.update_teststep_variables_mapping(variable_name,
                                                   variable_evel_value)

    def eval_content(self, content):
        '''
        evaluate content recursively, take effect on each variable and function in content.
        content may be in any data structure, include dict, list, tuple, num, str, etc.
        '''

        return parser.parse_data(content, self.teststep_variables_mapping,
                                 self.TESTCASE_SHARED_FUNCTIONS_MAPPING)

    def update_testcase_runtime_variables_mapping(self, variables):
        '''
        update testcase_runtime_variables_mapping with extracted variables in teststep.
        Args:
            variables (OrderedDict): extracted variable in teststep
        '''

        for variable_name, variable_value in variables.items():
            self.testcase_runtime_variables_mapping[
                variable_name] = variable_value
            self.update_teststep_variables_mapping(variable_name,
                                                   variable_value)

    def update_teststep_variables_mapping(self, variable_name, variable_value):
        '''
        bind and update testcase variables mapping to teststep_variables_mapping
        '''
        self.teststep_variables_mapping[variable_name] = variable_value

    def get_parsed_request(self, request_dict, level='teststep'):
        '''
        get parsed request with variables and functions.
        Args:
            request_dict (dict): request config mapping
            level (enum): 'testcase' or 'teststep'
        Returns:
            dict: parsed request dict
        '''

        if level == 'testcase':
            # testcase config request dict has been parsed in parse_tests
            self.TESTCASE_SHARED_REQUSET_MAPPING = copy.deepcopy(request_dict)
            return self.TESTCASE_SHARED_REQUSET_MAPPING
        else:
            # teststep
            return self.eval_content(
                utils.deep_update_dict(
                    copy.deepcopy(self.TESTCASE_SHARED_REQUSET_MAPPING),
                    request_dict))

    def __eval_check_item(self, validator, resp_obj):
        '''
        evaludate check item in validator.
        Args:
            validator (dict): validator
                {'check':'status_code','comparator':'eq','expect':200}
                {'check':'$resp_body_success','comparator':'eq','expect':True}
        Returns:
            dict: validator info
                {
                    'check':'status_code',
                    'check_value':200,
                    'expect':201,
                    'comparator':'eq'
                }
        '''
        check_item = validator['check']
        # check_item should only be the following 5 formats:
        # 1. variable reference, e.g. $token
        # 2. function reference, e.g. ${is_status_code_200($status_code)}
        # 3. dict or list, may containing variable/function reference, e.g. {'var':'$abc'}
        # 4. string joined by delimiter. e.g. 'status_code', 'headers.content-type'
        # 5. regex string e.g. 'LB[\d]*(.*)RB[\d]*'

        if isinstance(check_item, (dict, list)) \
            or parser.extract_variables(check_item) \
                or parser.extract_functions(check_item):
            # format 1/2/3
            check_value = self.eval_content(check_item)
        else:
            # format 4/5
            check_value = resp_obj.extract_field(check_item)

        validator['check_value'] = check_value

        # expect_value should only be in 2 types:
        # 1. variable reference, e.g. $expect_status_code
        # 2. actual value e.g. 200
        expect_value = self.eval_content(validator['expect'])
        validator['expect'] = expect_value
        validator['check_result'] = 'unchecked'

        return validator

    def _do_validation(self, validator_dict):
        '''
        validator with functions
        Args:
            validator_dict (dict): validator dict
                {
                    'check':'status_code',
                    'check_value':200,
                    'expect':201,
                    'comparator':'eq'
                }
        '''

        comparator = utils.get_uniform_comparator(validator_dict['comparator'])
        validate_func = self.TESTCASE_SHARED_FUNCTIONS_MAPPING.get(comparator)

        if not validate_func:
            raise exceptions.FunctionNotFound(
                f'comparator not found: {comparator}')

        check_item = validator_dict['check']
        check_value = validator_dict['check_value']
        expect_value = validator_dict['expect']

        if (check_value is None or expect_value is None) \
                and comparator not in ['equals']:
            raise exceptions.ParamError(
                'Null value can only be comparated with comparator: eq/equals/==/is'
            )

        validate_msg = 'validator: {} {} {} {}'.format(
            check_item, comparator, expect_value,
            type(expect_value).__name__)

        try:
            validator_dict['check_result'] = 'pass'
            validate_func(check_value, expect_value)
            validate_msg += '\t==> pass'
            logger.log_debug(validate_msg)
        except (AssertionError, TypeError):
            validate_msg += '\t==> fail'
            validate_msg += '\n{}({}) {} {}({})'.format(
                check_value,
                type(check_value).__name__, comparator, expect_value,
                type(expect_value).__name__)
            logger.log_error(validate_msg)
            validator_dict['check_result'] = 'fail'
            raise exceptions.VaildationFailure(validate_msg)

    def validate(self, validators, resp_obj):
        '''
        make validations
        '''

        evaluated_validators = []
        if not validators:
            return evaluated_validators

        logger.log_info('start to validate.')
        validate_pass = True

        for vaildator in validators:
            # evaluate validators with context variable mapping.
            evaluated_validator = self.__eval_check_item(
                parser.parse_validator(vaildator), resp_obj)

            try:
                self._do_validation(evaluated_validator)
            except exceptions.VaildationFailure:
                validate_pass = False

            evaluated_validators.append(evaluated_validator)

        if not validate_pass:
            raise exceptions.VaildationFailure
