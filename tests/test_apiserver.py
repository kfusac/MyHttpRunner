import random
import requests

from tests.base import TestApiServerBase


class TestApiServer(TestApiServerBase):
    @classmethod
    def setup_class(cls):
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        super().teardown_class()

    def setup_method(self):
        self.headers = self.get_authenticated_headers()
        self.reset_all()

    def test_index(self):
        resp = self.api_client.get(self.host)
        assert resp.status_code == 200

    def test_rest_all(self):
        resp = self.reset_all()
        assert resp.status_code == 200
        assert resp.json()['success']

    def test_create_user_not_existed(self):
        resp = self.create_user(1000, 'user1', '123456')
        assert resp.status_code == 201
        assert resp.json()['success']

    def test_create_user_existed(self):
        resp = self.create_user(1000, 'user1', '123456')
        resp = self.create_user(1000, 'user1', '123456')
        assert resp.status_code == 500

    def test_get_users_empty(self):
        resp = self.get_users()
        assert resp.status_code == 200
        assert resp.json()['count'] == 0

    def test_get_users_not_empty(self):
        resp = self.create_user(1000, 'user1', '123456')
        resp = self.get_users()
        assert resp.status_code == 200
        assert resp.json()['count'] == 1

        resp = self.create_user(1001, 'user2', '123456')
        resp = self.get_users()
        assert resp.status_code == 200
        assert resp.json()['count'] == 2

    def test_get_user_not_existed(self):
        resp = self.get_user(1000)
        assert resp.status_code == 404
        assert not resp.json()['success']

    def test_get_user_existed(self):
        self.create_user(1000, 'user1', '123456')
        resp = self.get_user(1000)
        assert resp.status_code == 200
        assert resp.json()['success']

    def test_update_user_not_existed(self):
        resp = self.update_user(1000, 'user1', '123456')
        assert resp.status_code == 404
        assert not resp.json()['success']

    def test_update_user_existed(self):
        self.create_user(1000, 'user1', '123456')
        resp = self.update_user(1000, 'user2', '123456')
        assert resp.status_code == 200
        assert resp.json()['data']['name'] == 'user2'

    def test_delete_user_not_existed(self):
        resp = self.delete_user(1000)
        assert resp.status_code == 404
        assert not resp.json()['success']

    def test_delete_user_existed(self):
        self.create_user(1000, 'leo', '123456')
        resp = self.delete_user(1000)
        assert resp.status_code == 200
        assert resp.json()['success']

    def reset_all(self):
        url = f'{self.host}/api/reset-all'
        return self.api_client.get(url, headers=self.headers)

    def get_users(self):
        url = f'{self.host}/api/users'
        return self.api_client.get(url, headers=self.headers)

    def create_user(self, uid, name, password):
        url = f'{self.host}/api/users/{uid}'
        data = {'name': name, 'password': password}
        return self.api_client.post(url, json=data, headers=self.headers)

    def get_user(self, uid):
        url = f'{self.host}/api/users/{uid}'
        return self.api_client.get(url, headers=self.headers)

    def update_user(self, uid, name, password):
        url = f'{self.host}/api/users/{uid}'
        data = {'name': name, 'password': password}
        return self.api_client.put(url, json=data, headers=self.headers)

    def delete_user(self, uid):
        url = f'{self.host}/api/users/{uid}'
        return self.api_client.delete(url, headers=self.headers)
