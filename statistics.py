from django.utils import timezone
from data.models import ExecutorStatistics, Executor
import logging


def update_statistic(executor: Executor, ready_min: int = None, work_min: int = None, done_task: int = None,
                     mass_task: int = None, postponed_task: int = None, cancel_task: int = None):
    logging.debug("Update statistic...")
    date = timezone.now().date()
    statistic = ExecutorStatistics.objects.get_or_create(executor=executor, date=date)[0]
    if ready_min:
        statistic.ready_min += ready_min
    if work_min:
        statistic.work_min += work_min
    if done_task:
        statistic.done_tasks += done_task
    if mass_task:
        statistic.mass_tasks += mass_task
    if postponed_task:
        statistic.postponed_tasks += postponed_task
    if cancel_task:
        statistic.cancel_tasks += cancel_task
    statistic.save()
    logging.debug("Statistic updated!")