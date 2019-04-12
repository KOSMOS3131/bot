from .utils import *


def get_task_priority():
    result = make_request('get', f'taskpriority')
    return result if type(result) is not APIError else result
