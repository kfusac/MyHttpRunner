from tests.api_server import SECRET_KEY, gen_md5, get_sign, HTTPBIN_SERVER


def is_status_code_200(status_code):
    return status_code == 200


def sum_status_code(status_code, expect_num):
    '''
    sum status code digites
    e.g. 400 => 4, 201 => 3
    '''

    sum_value = 0
    for digit in str(status_code):
        sum_value += int(digit)

    assert sum_value == expect_num


def hook_print(msg):
    print(msg)
