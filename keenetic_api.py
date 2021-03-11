import hashlib
from hashlib import sha256
from typing import Dict
from urllib import parse

from requests import Session


class KeeneticClient:

    def __init__(self, admin_endpoint: str, skip_auth: bool, login: str, password: str):
        self._admin_endpoint = admin_endpoint
        self._skip_auth = skip_auth
        self._login = login
        self._password = password

    def __enter__(self):
        self._session = Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            self._session.close()

    def _auth(self) -> bool:
        if self._skip_auth:
            return True
        auth_endpoint = f"{self._admin_endpoint}/auth"
        check_auth_response = self._session.get(auth_endpoint)
        if check_auth_response.status_code == 401:
            ndm_challenge = check_auth_response.headers.get('X-NDM-Challenge')
            ndm_realm = check_auth_response.headers.get('X-NDM-Realm')
            md5 = hashlib.md5((self._login + ':' + ndm_realm + ':' + self._password).encode('utf-8')).hexdigest()
            sha = sha256((ndm_challenge + md5).encode('utf-8')).hexdigest()
            auth_response = self._session.post(auth_endpoint, json={'login': self._login, 'password': sha})
            if auth_response.status_code == 200:
                return True
            else:
                raise ConnectionError(f"Keenetic authorisation failed. Status {auth_response.status_code}")
        elif check_auth_response.status_code == 200:
            return True
        raise ConnectionError(f"Failed to check authorisation, status unknown ({check_auth_response.status_code})")

    def metric(self, command: str, params: Dict) -> Dict:
        if self._auth():
            url = f"{self._admin_endpoint}/rci/show/{command.replace(' ', '/')}" + "?" + parse.urlencode(
                params)
            r = self._session.get(url)
            if r.status_code == 200:
                return r.json()
            raise KeeneticApiException(r.status_code, r.text)
        else:
            raise ConnectionError(f"No keenetic connection.")


class KeeneticApiException(Exception):

    def __init__(self, status_code: int, response_text: str):
        self.status_code = status_code
        self.response_text = response_text
