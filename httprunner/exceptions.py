# !/usr/bin/python
# -*- coding: utf-8 -*-

from json import JSONDecodeError


###############################################################################
#   failure type exceptions
#   these exceptions will mark test as failure
###############################################################################
class MyBaseFailure(Exception):
    pass


class VaildationFailure(MyBaseFailure):
    pass


class ExtractFailure(MyBaseFailure):
    pass


class SetupHooksFailure(MyBaseFailure):
    pass


class TeardownHooksFailure(MyBaseFailure):
    pass


###############################################################################
#   error type exceptions
#   there exceptions will mark test a error
###############################################################################


class MyBaseError(Exception):
    pass


class FileFormatError(MyBaseError):
    pass


class ParamError(MyBaseError):
    pass


class NotFoundError(MyBaseError):
    pass


class FileNotFound(FileNotFoundError, NotFoundError):
    pass


class FunctionNotFound(NotFoundError):
    pass


class VariableNotFound(NotFoundError):
    pass


class ApiNotFound(NotFoundError):
    pass


class TestcaseNotFound(NotFoundError):
    pass
