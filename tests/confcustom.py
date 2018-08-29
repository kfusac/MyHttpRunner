from tests.api_server import SECRET_KEY


def is_status_code_200(status_code):
    return status_code == 200


def hook_print(msg):
    print(msg)
