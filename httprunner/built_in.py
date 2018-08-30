import random
import string
import time
import re

###############################################################################
#   built-in functions
###############################################################################


def gen_random_string(str_len):
    '''
    generate random string with specified length.
    '''
    return ''.join(
        random.choice(string.ascii_letters + string.digits)
        for _ in range(str_len))


def get_timestamp(str_len=13):
    '''
    get timestamp string, length can onlt between 0 and 16
    '''

    if isinstance(str_len, int) and 0 < str_len < 17:
        return str(time.time()).replace('.', '')[:str_len]


###############################################################################
#   built-in comparators
###############################################################################


def equals(check_value, expect_value):
    assert check_value == expect_value


def less_than(check_value, expect_value):
    assert check_value < expect_value


def less_than_or_equals(check_value, expect_value):
    assert check_value <= expect_value


def greater_than(check_value, expect_value):
    assert check_value > expect_value


def greater_than_or_equals(check_value, expect_value):
    assert check_value >= expect_value


def not_equals(check_value, expect_value):
    assert check_value != expect_value


def string_equals(check_value, expect_value):
    assert str(check_value) == str(expect_value)


def length_equals(check_value, expect_value):
    assert isinstance(expect_value, int)
    assert len(check_value) == expect_value


def length_less_than(check_value, expect_value):
    assert isinstance(expect_value, int)
    assert len(check_value) < expect_value


def length_less_than_or_equals(check_value, expect_value):
    assert isinstance(expect_value, int)
    assert len(check_value) <= expect_value


def length_greater_than(check_value, expect_value):
    assert isinstance(expect_value, int)
    assert len(check_value) > expect_value


def length_greater_than_or_equals(check_value, expect_value):
    assert isinstance(expect_value, int)
    assert len(check_value) >= expect_value


def contains(check_value, expect_value):
    assert isinstance(check_value, (list, tuple, set, str))
    assert expect_value in check_value


def contains_by(check_value, expect_value):
    assert isinstance(expect_value, (list, tuple, set, str))
    assert check_value in expect_value


def type_match(check_value, expect_value):
    def get_type(name):
        if isinstance(name, type):
            return name
        elif isinstance(name, str):
            try:
                return __builtins__[name]
            except KeyError:
                raise ValueError(name)
        else:
            raise ValueError(name)

    assert isinstance(check_value, get_type(expect_value))


def regex_match(check_value, expect_value):
    assert isinstance(expect_value, str)
    assert isinstance(check_value, str)
    assert re.match(expect_value, check_value)


def startswith(check_value, expect_value):
    assert str(check_value).startswith(str(expect_value))


def endswith(check_value, expect_value):
    assert str(check_value).endswith(str(expect_value))


###############################################################################
#   built-in hook
###############################################################################
def sleep_N_secs(n_secs):
    '''
    sleep n seconds
    '''

    time.sleep(n_secs)
