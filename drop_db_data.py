import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()

from data.models import *

BlockageJournal.objects.all().delete()

for executor in Executor.objects.all():
    if not executor.status == 'Не готов':
        executor.status = 'Готов'
    executor.intraservice_task_active = None
    executor.save()

ExecutorStatistics.objects.all().delete()

IntraserviceTask.objects.all().delete()

Journal.objects.all().delete()

Statistic.objects.all().delete()
