from .utils import *


def get_user(user_id: int):  # ToDo
    return make_request('get', f'user/{user_id}')

