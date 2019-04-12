from typing import List

from django.db.models import Q
from data.models import Executor


def get_ready_executors() -> List[Executor]:
    return Executor.objects.filter(Q(status="Готов") | Q(status="Занят"))


def get_free_executors() -> List[Executor]:
    return Executor.objects.filter(status="Готов")


def get_working_executors() -> List[Executor]:
    return Executor.objects.filter(status="Занят")
