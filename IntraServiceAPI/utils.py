import datetime
import requests
import json
from typing import List

from IntraServiceAPI import config


class APIError(Exception):
    def __init__(self, msg, url=None, params=None):
        self.msg = json.loads(msg)["Message"]
        self.url = url
        self.params = params

    def __str__(self):
        return f"APIError({self.msg}, {str(self.params)})"


def make_request(type_: str, resource: str, params: dict = None, files: dict = None, json_k: json = None) -> json:
    url = f'{config.BASIC_URL}/api/{resource}'
    verify = True
    try:
        if type_ == 'get':
            r = requests.get(url, params=params, verify=verify, auth=(config.API_LOGIN, config.API_PASSWORD),
                             headers=config.HEADERS, json=json_k)
        elif type_ == 'post':
            r = requests.post(url, params=params, verify=verify, auth=(config.API_LOGIN, config.API_PASSWORD),
                              headers=config.HEADERS, files=files, json=json_k)
        elif type_ == 'put':
            r = requests.put(url, params=params, verify=verify, auth=(config.API_LOGIN, config.API_PASSWORD),
                             headers=config.HEADERS, json=json_k)
        else:
            raise Exception(f'Wrong request type: {type_}')
        if r.status_code // 100 == 2:
            return r.json()
        else:
            raise APIError(r.content.decode("utf8"), url, params)
    except requests.ConnectionError as e:
        raise APIError(e, url, params)


def datetime_to_str(date: datetime) -> str:
    return date.strftime('%Y-%m-%d %H:%M')


def list_to_str(fields: List[str or int], separator: str = ',') -> str:
    result = str(fields[0])
    for f in fields[1:]:
        result += separator + str(f)
    return result
