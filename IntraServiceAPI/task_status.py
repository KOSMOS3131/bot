from .utils import *


def get_task_status():
    result = make_request('get', f'taskstatus')
    return result if type(result) is not APIError else result
