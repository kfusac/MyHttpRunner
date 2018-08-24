import multiprocessing
import time

import requests
from tests.api_server import FLASK_APP_PORT, HTTPBIN_HOST, HTTPBIN_PORT
from tests.api_server import app as flask_app
from tests.api_server import gen_md5, gen_random_string, get_sign, httpbin_app


def run_flask():
    flask_app.run(port=FLASK_APP_PORT)


def run_httpbin():
    if httpbin_app:
        httpbin_app.run(host=HTTPBIN_HOST, port=HTTPBIN_PORT)


class TestApiServerBase:
    @classmethod
    def setup_class(cls):
        cls.host = f'http://127.0.0.1:{FLASK_APP_PORT}'
        cls.flask_process = multiprocessing.Process(target=run_flask)
        cls.httpbin_process = multiprocessing.Process(target=run_httpbin)
        cls.flask_process.start()
        cls.httpbin_process.start()
        time.sleep(0.1)
        cls.api_client = requests.Session()

    @classmethod
    def teardown_class(cls):
        cls.flask_process.terminate()
        cls.httpbin_process.terminate()

    def get_token(self, user_agent, device_sn, os_platform, app_version):
        url = f'{self.host}/api/get-token'
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            'device_sn': device_sn,
            'os_platform': os_platform,
            'app_version': app_version
        }
        data = {
            'sign': get_sign(user_agent, device_sn, os_platform, app_version)
        }
        resp = self.api_client.post(url, json=data, headers=headers)
        resp_json = resp.json()
        assert resp_json['success']
        assert 'token' in resp_json
        assert len(resp_json['token']) == 16
        return resp_json['token']

    def get_authenticated_headers(self):
        user_agent = 'ios/10.3'
        device_sn = gen_random_string(15)
        os_platform = 'ios'
        app_version = '2.8.6'

        token = self.get_token(user_agent, device_sn, os_platform, app_version)
        headers = {'device_sn': device_sn, 'token': token}
        return headers
