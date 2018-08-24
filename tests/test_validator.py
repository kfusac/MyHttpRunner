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
