# !/usr/bin/python
# -*- coding: utf-8 -*-

import pytest

from httprunner import validator


class TestValidator:
    def test_is_testcases(self):
        data_structure = 'path/to/file'
        assert not validator.is_testcases(data_structure)
        data_structure = ['path/to/file1', 'path/to/file2']
        assert not validator.is_testcases(data_structure)

        data_structure = {
            "name": "desc1",
            "config": {},
            "api": {},
            "teststeps": ["testcase1", "testcase2"]
        }
        assert validator.is_testcases(data_structure)

        data_structure = [{
            "name": "desc1",
            "config": {},
            "api": {},
            "teststeps": ["testcase11", "testcase12"]
        }, {
            "name": "desc2",
            "config": {},
            "api": {},
            "teststeps": ["testcase21", "testcase22"]
        }]
        assert validator.is_testcases(data_structure)

    def test_is_variable(self):
        var1 = 123
        var2 = 'abc'
        assert validator.is_variable(('var1', var1))
        assert validator.is_variable(('var2', var2))

        __var = 123
        assert validator.is_variable(('__var', __var))

        func = lambda x: x + 1
        assert not validator.is_variable(('func', func))

        assert not validator.is_variable(('pytest', pytest))

    def test_is_function(self):
        func = lambda x: x + 1
        assert validator.is_function(('func', func))
        assert validator.is_function(('validator.is_testcase'),
                                     validator.is_testcase)
