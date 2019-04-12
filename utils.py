import os
import sys

from django.core.exceptions import ObjectDoesNotExist
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()


from data.models import *


class TaskMethods:
    @classmethod
    def show(cls):
        for task in IntraserviceTask.objects.all():
            print(f'{task.id:5} | {task.get_status_display():10}({task.status:2}) | '
                  f'{PRIORITY_STATUSES_R[task.priority]:10}')

    @classmethod
    def delete(cls):
        id_ = int(input('Введите id: '))
        task = IntraserviceTask.objects.get(id=id_)
        for ex in Executor.objects.filter(intraservice_task_active=task):
            ex.intraservice_task_active = None
            ex.save()
        task.delete()


class ExecutorMethods:
    @classmethod
    def show(cls):
        for ex in Executor.objects.all():  # type: Executor
            if not ex.intraservice_task_active:
                print(f'{ex.intraservice_user.name:35} | {ex.status:9} | {ex.intraservice_user.id:4} |')
            else:
                print(f'{ex.intraservice_user.name:35} | {ex.status:9} | {ex.intraservice_user.id:4} | '
                      f'{ex.intraservice_task_active.id}')

    @classmethod
    def add(cls):
        while True:
            username = input('Введите username: ')
            try:
                telegram_user = TelegramUser.objects.get(username=username)
            except ObjectDoesNotExist:
                print('Пользователь не найден!')
            else:
                print('Пользователь найден!')
                break
        i_id = int(input('Введите id(intraservice): '))
        name = input('Введите ФИО: ')
        try:
            intraservice_user = IntraserviceUser.objects.get(id=i_id)
            intraservice_user.name = name
            intraservice_user.save()
        except ObjectDoesNotExist:
            intraservice_user = IntraserviceUser.objects.create(name=name, id=i_id)
        e = Executor.objects.create(intraservice_user=intraservice_user, telegram_user=telegram_user, status='Не готов')
        e.save()

    @classmethod
    def delete(cls):
        while True:
            id_ = int(input('Введите intraservice id:'))
            try:
                executor = Executor.objects.get(intraservice_user__id=id_)
            except ObjectDoesNotExist:
                print('Сотрудник не найден!')
            else:
                print('Сотрудник найден!')
                break
        executor.delete()


class UserMethods:
    @classmethod
    def add(cls):
        while True:
            try:
                user_id = int(input("Введите telegram_id: "))
                user = TelegramUser.objects.get(user_id=user_id)
            except ObjectDoesNotExist:
                user = TelegramUser.objects.create(user_id=user_id)
                telegram_username = input("Введите username: ")
            finally:
                user.username = telegram_username
                user.save()
                print("Добавлен!")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Wrong args!')
    else:
        if sys.argv[1] == 'task':
            if sys.argv[2] == 'show':
                TaskMethods.show()
            elif sys.argv[2] == 'delete':
                TaskMethods.delete()
        elif sys.argv[1] == 'executor':
            if sys.argv[2] == 'show':
                ExecutorMethods.show()
            elif sys.argv[2] == 'add':
                ExecutorMethods.add()
            elif sys.argv[2] == 'del':
                ExecutorMethods.delete()
