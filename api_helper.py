from bot_settings import API_LOGIN, API_PASSWORD, EVALUATIONS, SERVER_URL, MASS_PROBLEMS_SERVICE_IDS, MASS_PROBLEMS_TASK_TYPE_ID
from datetime import datetime
import IntraServiceAPI

# Django specific settings
import os


# Ensure settings are read
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()

# Your application specific imports
from data.models import *


class Api(object):
    def __init__(self):
        self.new_api = IntraServiceAPI
        self.new_api.config.API_LOGIN = API_LOGIN
        self.new_api.config.API_PASSWORD = API_PASSWORD
        self.new_api.config.BASIC_URL = SERVER_URL
        self.auth = (API_LOGIN, API_PASSWORD)
        self.url = SERVER_URL

    def get_task_info(self, task):
        return self.new_api.get_task(task.intraservice_task_id)

    def get_task(self, intraservice_task: IntraserviceTask):
        return self.new_api.get_task(intraservice_task.id)

    def get_last_editor(self, task_id):
        return self.new_api.get_task_lifetime(task_id, last_comments_on_top=True)[0]['Editor']

    def get_task_lifetime(self, task):
        return self.new_api.get_task_lifetime(task.id, last_comments_on_top=True)

    def get_status_editor(self, task: IntraserviceTask, status):
        lifetimes = self.get_task_lifetime(task)
        for lt in lifetimes:
            if lt.get('StatusId') and lt.get('Editor'):
                if lt['StatusId'] == status:
                    return lt["Editor"]

    def get_deadline_editor(self, task: IntraserviceTask, deadline):
        lifetimes = self.get_task_lifetime(task)
        for lt in lifetimes:
            if lt.get('Deadline') and lt.get('Editor'):
                if datetime.strptime(lt["Deadline"], '%Y-%m-%dT%H:%M:%S') == deadline:
                    return lt['Editor']

    def create_task(self, task: TelegramTask):
        if task.screenshot:
            files = [('screenshot.jpg', open(task.screenshot.url, 'rb'))]
        else:
            files = None

        service_id = MASS_PROBLEMS_SERVICE_IDS[task.description]
        tesk_type_id = MASS_PROBLEMS_TASK_TYPE_ID[task.description]

        if not task.executor:
            return self.new_api.create_task(name=task.name(), service_id=service_id,
                                            status_id=TASK_STATUSES['Открыта'],
                                            priority_id=task.priority, type_id=tesk_type_id,
                                            description=task.intraservice_description(), files=files)['Task']
        else:
            return self.new_api.create_task(name=task.name(), service_id=service_id,
                                            status_id=TASK_STATUSES['Открыта'],
                                            priority_id=task.priority, type_id=tesk_type_id,
                                            description=task.intraservice_description(), files=files,
                                            executor_ids=[task.executor.intraservice_user.id])['Task']

    def get_tasks(self, date: datetime = None, filter_id: int = None):
        if date:
            date = [self.new_api.changed_more_than(date)]
        return self.new_api.get_tasks(
            filter_fields=date,
            sort_list=[self.new_api.desc(self.new_api.fields.priority_id),  # sort by PriorityId
                       self.new_api.asc(self.new_api.fields.created)],  # sort by Created
            filter_id=filter_id,
            pagesize=200
        )

    def send_task_review(self, task: IntraserviceTask or str, rating):
        rating = rating.replace("'", "")
        rating_id = EVALUATIONS[rating]
        if type(task) == str:
            self.new_api.change_task(int(task), evaluation_id=rating_id)
        else:
            self.new_api.change_task(task.id, evaluation_id=rating_id)
            task.delete()

    def update_executor_and_status(self, task_id, executor_id, status):
        return self.new_api.change_task(task_id, executor_ids=[executor_id],
                                        status_id=status)
