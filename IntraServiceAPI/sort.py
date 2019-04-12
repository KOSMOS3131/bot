from typing import List


class SortType:
    def __init__(self, field: str, type_: str):
        self.field = field
        self.type = type_

    def __str__(self):
        return f'{self.field} {self.type}'


def asc(field: str) -> SortType:
    return SortType(field, 'asc')


def desc(field: str) -> SortType:
    return SortType(field, 'desc')


def make_sort(sort_list: List[SortType]) -> str:
    result = str(sort_list[0])
    for sort in sort_list[1:]:
        result += ',' + str(sort)
    return result