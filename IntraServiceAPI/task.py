from . import FilterField
from . import sort
from .utils import *
from io import FileIO
from typing import List, Tuple


def get_tasks(service_id: int = None, fields: List[str] = None, search: str = None, archive: bool = None,
              inactive: bool = None, filter_id: int = None, sort_list: List[sort.SortType] = None,
              filter_fields: List[FilterField] = None, pagesize: int = None, page: int = None,
              include: List[str] = None) -> json or List[json]:
    params = {}
    if service_id is not None:
        params['service_id'] = service_id
    if fields is not None:
        params['fields'] = list_to_str(fields)
    if search is not None:
        params['search'] = search
    if archive is not None:
        params['archive'] = archive
    if inactive is not None:
        params['inactive'] = inactive
    if filter_id is not None:
        params['filterid'] = filter_id
    if sort_list is not None and sort:
        params['sort'] = sort.make_sort(sort_list)
    if filter_fields is not None:
        for ff in filter_fields:
            if ff.value:
                params[ff.type] = ff.value
    if pagesize is not None:
        params['pagesize'] = pagesize
    if page is not None:
        params['page'] = page
    if include is not None and include:
        params['include'] = list_to_str(include)
        return make_request('get', 'task', params)
    else:
        result = make_request('get', 'task', params)
        return result['Tasks'] if type(result) is not APIError else result


def get_task(id_: int, include: List[str] = None):
    params = {}
    if include is not None and include:
        params['include'] = list_to_str(include)
        return make_request('get', f'task/{id_}', params)
    else:
        result = make_request('get', f'task/{id_}', params)
        return result['Task'] if type(result) is not APIError else result


def get_new_task_example(service_id: int, tasktypeid: int, include: List[str] = None):
    params = {'serviceid': service_id,
              'tasktypeid': tasktypeid}
    if include is not None and include:
        params['include'] = list_to_str(include)
    return make_request('get', f'newtask', params)


def load_files(files: List[Tuple[str, FileIO]]):
    multipart_form_data = {}
    for i in range(len(files)):
        multipart_form_data[f'file{i}'] = (files[i][0], files[i][1], "multipart/form-data")
    result = make_request('post', 'TaskFile', files=multipart_form_data)
    return result['FileTokens'] if type(result) is not APIError else result


def create_task(name: str, service_id: int, status_id: int, priority_id: int, type_id: int,
                comment: str = None, deadline: datetime = None, description: str = None, parent_id: int = None,
                creator_id: int = None, service_stage_id: int = None, is_private_comment: bool = None,
                is_mass_incident: bool = None, completion_status: int = None, asset_ids: List[int] = None,
                category_ids: List[int] = None, executor_ids: List[int] = None, coordinator_ids: List[int] = None,
                executor_group_id: int = None, observer_ids: List[int] = None, files: List[Tuple[str, FileIO]] = None,
                deleted_files: List[str] = None):  # ToDo: Fields ?
    task = get_new_task_example(service_id, type_id)['Task']
    task['Name'] = name
    task['ServiceId'] = service_id
    task['StatusId'] = status_id
    task['PriorityId'] = priority_id
    task['TypeId'] = type_id
    if comment is not None:
        task['Comment'] = comment
    if deadline is not None:
        task['Deadline'] = datetime_to_str(deadline)
    if description is not None:
        task['Description'] = description
    if parent_id is not None:
        task['ParentId'] = parent_id
    if creator_id is not None:
        task['CreatorId'] = creator_id
    if service_stage_id is not None:
        task['ServiceStageId'] = service_stage_id
    if is_private_comment is not None:
        task['IsPrivateComment'] = is_private_comment
    if is_mass_incident is not None:
        task['IsMassIncident'] = is_mass_incident
    if completion_status is not None:
        task['CompletionStatus'] = completion_status
    if asset_ids is not None:
        task['AssetIds'] = asset_ids
    if category_ids is not None:
        task['CategoryIds'] = category_ids
    if executor_ids is not None and executor_ids:
        task['ExecutorIds'] = list_to_str(executor_ids)
    if coordinator_ids is not None and coordinator_ids:
        task['CoordinatorIds'] = list_to_str(coordinator_ids)
    if executor_group_id is not None:
        task['ExecutorGroupId'] = executor_group_id
    if observer_ids is not None and observer_ids:
        task['ObserverIds'] = list_to_str(observer_ids)
    if files is not None and files:
        task['FileTokens'] = load_files(files)
    if deleted_files is not None and deleted_files:
        task['DeletedFiles'] = list_to_str(deleted_files, '|')
    return make_request('post', 'task', json_k=task)


def change_task(id_: int, name: str = None, reason: int = None, service_id: int = None, status_id: int = None,
                priority_id: int = None, type_id: int = None, comment: str = None, deadline: datetime = None,
                description: str = None, parent_id: int = None, creator_id: int = None, service_stage_id: int = None,
                is_private_comment: bool = None, is_mass_incident: bool = None, completion_status: int = None,
                asset_ids: List[int] = None, category_ids: List[int] = None, executor_ids: List[int] = None,
                coordinator_ids: List[int] = None, executor_group_id: int = None, observer_ids: List[int] = None,
                files: List[Tuple[str, FileIO]] = None, deleted_files: List[str] = None, evaluation_id: int = None,
                reaction_date: datetime = None, reaction_date_fact: datetime = None,
                resolution_date_fact: datetime = None, coordinate: bool = None):
    task = {}
    if name is not None:
        task['Name'] = name
    if reason is not None:
        task["field1129"] = reason
    if service_id is not None:
        task['ServiceId'] = service_id
    if status_id is not None:
        task['StatusId'] = status_id
    if priority_id is not None:
        task['PriorityId'] = priority_id
    if type_id is not None:
        task['TypeId'] = type_id
    if comment is not None:
        task['Comment'] = comment
    if deadline is not None:
        task['Deadline'] = datetime_to_str(deadline)
    if description is not None:
        task['Description'] = description
    if parent_id is not None:
        task['ParentId'] = parent_id
    if creator_id is not None:
        task['CreatorId'] = creator_id
    if service_stage_id is not None:
        task['ServiceStageId'] = service_stage_id
    if is_private_comment is not None:
        task['IsPrivateComment'] = is_private_comment
    if is_mass_incident is not None:
        task['IsMassIncident'] = is_mass_incident
    if completion_status is not None:
        task['CompletionStatus'] = completion_status
    if asset_ids is not None:
        task['AssetIds'] = asset_ids
    if category_ids is not None:
        task['CategoryIds'] = category_ids
    if executor_ids is not None and executor_ids:
        task['ExecutorIds'] = list_to_str(executor_ids)
    if coordinator_ids is not None and coordinator_ids:
        task['CoordinatorIds'] = list_to_str(coordinator_ids)
    if executor_group_id is not None:
        task['ExecutorGroupId'] = executor_group_id
    if observer_ids is not None and observer_ids:
        task['ObserverIds'] = list_to_str(observer_ids)
    if files is not None and files:
        task['FileTokens'] = load_files(files)
    if deleted_files is not None and deleted_files:
        task['DeletedFiles'] = list_to_str(deleted_files, '|')
    if evaluation_id is not None:
        task['EvaluationId'] = evaluation_id
    if reaction_date is not None:
        task['ReactionDate'] = datetime_to_str(reaction_date)
    if reaction_date_fact is not None:
        task['ReactionDateFact'] = datetime_to_str(reaction_date_fact)
    if resolution_date_fact is not None:
        task['ResolutionDateFact'] = datetime_to_str(resolution_date_fact)
    if coordinate is not None:
        task['Coordinate'] = coordinate
    return make_request('put', f'task/{id_}', json_k=task)


def get_task_url(id_: int) -> str:
    return f'{config.BASIC_URL}/Task/View/{id_}'


def get_task_lifetime(taskid: int, include: List[str] = None, last_comments_on_top: bool = None):
    params = dict()
    params['taskid'] = taskid
    if last_comments_on_top is not None:
        params['lastcommentsontop'] = last_comments_on_top
    if include is not None and include:
        return make_request('get', 'tasklifetime', params=params)
    else:
        result = make_request('get', 'tasklifetime', params=params)
        return result['TaskLifetimes'] if type(result) is not APIError else result
