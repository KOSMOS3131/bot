from IntraServiceAPI.utils import *


class FilterField:
    def __init__(self, type_: str, value):
        self.type = type_
        self.value = value


def changed_less_than(date: datetime) -> FilterField:
    return FilterField('ChangedLessThan', datetime_to_str(date))


def changed_more_than(date: datetime) -> FilterField:
    return FilterField('ChangedMoreThan', datetime_to_str(date))


def changed(date: datetime) -> FilterField:
    return FilterField('Changed', datetime_to_str(date))


def created_less_than(date: datetime) -> FilterField:
    return FilterField('CreatedLessThan', datetime_to_str(date))


def created_more_than(date: datetime) -> FilterField:
    return FilterField('CreatedMoreThan', datetime_to_str(date))


def created(date: datetime) -> FilterField:
    return FilterField('Created', datetime_to_str(date))


def closed_less_than(date: datetime) -> FilterField:
    return FilterField('ClosedLessThan', datetime_to_str(date))


def closed_more_than(date: datetime) -> FilterField:
    return FilterField('ClosedMoreThan', datetime_to_str(date))


def closed(date: datetime) -> FilterField:
    return FilterField('Closed', datetime_to_str(date))


def deadline_less_than(date: datetime) -> FilterField:
    return FilterField('DeadlineLessThan', datetime_to_str(date))


def deadline_more_than(date: datetime) -> FilterField:
    return FilterField('DeadlineMoreThan', datetime_to_str(date))


def deadline(date: datetime) -> FilterField:
    return FilterField('Deadline', datetime_to_str(date))


def reaction_date_less_than(date: datetime) -> FilterField:
    return FilterField('ReactionDateLessThan', datetime_to_str(date))


def reaction_date(date: datetime) -> FilterField:
    return FilterField('ReactionDate', datetime_to_str(date))


def resolution_overdue(val: bool) -> FilterField:
    return FilterField('ResolutionOverdue', val)


def reaction_overdue(val: bool) -> FilterField:
    return FilterField('ReactionOverdue', val)


def type_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('TypeIds', ids)


def status_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('StatusIds', ids)


def priority_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('PriorityIds', ids)


def service_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('ServiceIds', ids)


def editor_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('EditorIds', ids)


def creator_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('CreatorIds', ids)


def executor_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('ExecutorIds', ids)


def executor_group_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('ExecutorGroupIds', ids)


def observer_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('ObserverIds', ids)


def category_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('CategoryIds', ids)


def assets_ids(ids: List[int]):
    ids = list_to_str(ids) if ids else None
    return FilterField('AssetsIds', ids)
