from django.utils import timezone
from data.models import Journal, Executor


def add_journal_record(executor: Executor):
    Journal.objects.create(executor=executor, from_time=executor.last_status_change,
                           to_time=timezone.now(), status=executor.status)
