from typing import List

from django.db.models import Q

from data.models import IntraserviceTask, TASK_STATUSES, EXECUTOR_GROUP_IDS


def get_opened_tasks() -> List[IntraserviceTask]:
    return IntraserviceTask.objects.filter(status=TASK_STATUSES["Открыта"]).filter(
        executor_group=EXECUTOR_GROUP_IDS['Техподдержка'])


def get_mass_tasks() -> List[IntraserviceTask]:
    return IntraserviceTask.objects.filter(is_mass=True).filter(executor_group=EXECUTOR_GROUP_IDS['Техподдержка']).filter(status=TASK_STATUSES["Открыта"])
