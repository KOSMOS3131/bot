from threading import Thread, Event
from datetime import timedelta
import logging
import time
from api_helper import Api
from multiprocessing.dummy import Pool as ThreadPool

import keyboards as kb
import responses as r

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db import connection

from data.models import *

import telebot
from bot_settings import UPDATE_TIME, NOTIFY_TASK_MIN, MAX_TASK_MIN, MASS_PROBLEMS, SEC_TO_PIN, \
    ADMINS_FOR_NOTIFICATION, BOT_TOKEN

from statistics import update_statistic
from journal import add_journal_record
from executor import get_ready_executors
from task import get_opened_tasks, get_mass_tasks

from IntraServiceAPI.utils import APIError

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s : %(levelname)s : %(message)s", filename="./logs/bot.log")

api = Api()
bot = telebot.TeleBot(token=BOT_TOKEN)


class TaskListener(Thread):
    def __init__(self):
        logging.info('Init TaskListener thread...')
        super().__init__()
        self.daemon = True
        self.update_enable = Event()
        self.create_task_enable = Event()
        self.run_enabled = True
        self.new_task_count = 0
        self.blockage = False
        self.blockage_start_time = None
        logging.debug('TaskListener thread inited!')

    def stop(self):
        self.run_enabled = False

    def blockage_notify(self):
        # Оповещения о завалах
        if len(get_opened_tasks()) >= 5:
            if not self.blockage:
                self.blockage_start_time = timezone.now()
                if len(get_ready_executors()):
                    message_to_admins(('🆘 Начался завал в работе сотрудников ТП: '
                                       'уже больше 5 открытых заявок и все сотрудники заняты'))
                else:
                    message_to_admins(('🆘 Начался завал в работе сотрудников ТП: '
                                       'уже больше 5 открытых заявок и все сотрудники отсутствуют'))
            self.blockage = True
        else:
            if self.blockage:
                message_to_admins('🆗 Закончился завал в работе сотрудников ТП')
                BlockageJournal.objects.create(from_time=self.blockage_start_time, to_time=timezone.now())
            self.blockage = False

    def task_sync(self, task: IntraserviceTask):
        logging.debug(f'Sync {task}...')
        try:
            intr_task = api.new_api.get_task(task.id)
        except api.new_api.APIError as e:
            logging.error(e)
            return
        else:
            self.processing_update(intr_task)
            logging.debug(f'{task} synced!')
            connection.close()

    @staticmethod
    def postponed_notify():
        # Оповещение о большом количестве отложенных задач
        logging.debug('Postponed task notify...')
        for ex in Executor.objects.filter(executorstatistics__postponed_notify=False).filter(
                executorstatistics__date=timezone.now().date()).filter(executorstatistics__postponed_tasks__gt=9):
            statistic = ExecutorStatistics.objects.get(executor=ex, date=timezone.now().date())
            if not statistic.postponed_notify and statistic.postponed_tasks > 9:
                message_to_admins("Я сейчас обнаружил, что {name} отложил за смену более 9 заявок.".format(
                    name=ex.intraservice_user.name))
                bot.send_message(ex.telegram_user.user_id,
                                 text=('Вы отложили слишком много заявок.\n'
                                       'Уведомление об этом поступило Вашему руководителю для разбирательства.'))
                statistic.postponed_notify = True
                statistic.save()
        logging.debug('Postponed task notified!')

    @staticmethod
    def pin_critical_tasks():
        # Раздаем критические задания
        free_executors = list(
            Executor.objects.filter(status='Готов').filter(intraservice_task_active=None).filter(
                last_status_change__lte=(timezone.now() - timedelta(seconds=SEC_TO_PIN))).order_by(
                '-last_status_change'))
        executors = list(Executor.objects.filter(status='Занят').filter(
            Q(intraservice_task_active__priority=PRIORITY_STATUSES['Низкий']) |
            Q(intraservice_task_active__priority=PRIORITY_STATUSES['Средний'])
        ).order_by('-last_status_change'))
        for task in IntraserviceTask.objects.filter(status=TASK_STATUSES['Открыта']).filter(
                priority=PRIORITY_STATUSES['Критический']).filter(parent_id=None).filter(
                executor_group=EXECUTOR_GROUP_IDS['Техподдержка']).order_by('created'):
            if len(free_executors) == 0:
                if len(executors) == 0:
                    break
                else:
                    pin_critical_task(executors.pop(), task)
            else:
                pin_to_task(free_executors.pop(), task)
            free_executors = list(
                Executor.objects.filter(status='Готов').filter(intraservice_task_active=None).filter(
                    last_status_change__lte=(timezone.now() - timedelta(seconds=SEC_TO_PIN))).order_by(
                    '-last_status_change'))
            executors = list(Executor.objects.filter(status='Занят').filter(
                Q(intraservice_task_active__priority=PRIORITY_STATUSES['Низкий']) |
                Q(intraservice_task_active__priority=PRIORITY_STATUSES['Средний'])
            ).order_by('-last_status_change'))
            for t_task in IntraserviceTask.objects.filter(status=TASK_STATUSES['Открыта']).filter(
                    priority=PRIORITY_STATUSES['Критический']).filter(parent_id=None).filter(
                    executor_group=EXECUTOR_GROUP_IDS['Техподдержка']).order_by('created'):
                if len(free_executors) == 0:
                    if len(executors) == 0:
                        break
                    else:
                        pin_critical_task(executors.pop(), t_task)
                else:
                    pin_to_task(free_executors.pop(), t_task)

    @staticmethod
    def pin_non_critical_tasks():
        # Раздаем задания открытые задания
        executors = list(
            Executor.objects.filter(status='Готов').filter(intraservice_task_active=None).filter(
                last_status_change__lte=(timezone.now() - timedelta(seconds=SEC_TO_PIN))).order_by(
                '-last_status_change'))
        tasks = list(IntraserviceTask.objects.filter(status=TASK_STATUSES['Открыта']).filter(
            parent_id=None).filter(executor_group=EXECUTOR_GROUP_IDS['Техподдержка']))
        tasks = sorted(tasks)
        for task in tasks:
            if len(executors) == 0:
                break
            else:
                pin_to_task(executors.pop(), task)

    @staticmethod
    def group_mass_tasks():
        # Массовые проблемы
        for problem in MASS_PROBLEMS:
            problem_parent_task = None  # type: IntraserviceTask
            for task in IntraserviceTask.objects.filter(is_mass=True).filter(
                    created__gte=(timezone.now() - timedelta(minutes=30))).filter(
                    parent_id=None):
                if task.description:
                    if problem.lower() in task.description.lower():
                        problem_parent_task = task
                        break
            if problem_parent_task:  # Если массовая проблема уже существует
                for task in IntraserviceTask.objects.filter(created__gte=problem_parent_task.created).filter(
                        created__lte=(problem_parent_task.created + timedelta(minutes=30))).filter(
                        parent_id=None).filter(is_mass=False):
                    if task.description:
                        if problem.lower() in task.description.lower():
                            try:
                                executor = Executor.objects.get(intraservice_task_active=task)
                            except ObjectDoesNotExist:
                                pass
                            else:
                                close_task_after_mass(executor)
                            task.parent_id = task.id
                            api.new_api.change_task(task.id, parent_id=problem_parent_task.id, executor_group_id=3,
                                                    executor_ids=[])
                            task.save()
                            notify_client_mass_problem(task, problem)
            else:
                problem_tasks = []
                for task in IntraserviceTask.objects.filter(
                        created__gte=(timezone.now() - timedelta(minutes=10))).filter(parent_id=None):
                    if task.description and problem.lower() in task.description.lower():
                        problem_tasks.append(task)
                if len(problem_tasks) >= 5:
                    main_task = problem_tasks[0]
                    main_task.is_mass = True
                    api.new_api.change_task(main_task.id, is_mass_incident=True, executor_group_id=3,
                                            executor_ids=[])
                    main_task.save()
                    for ex in Executor.objects.filter(intraservice_task_active__in=problem_tasks):
                        close_task_after_mass(ex)
                    for task in problem_tasks:
                        if task.id == main_task.id:
                            continue
                        task.parent_id = main_task
                        api.new_api.change_task(task.id, parent_id=main_task.id, executor_group_id=3,
                                                executor_ids=[])
                        task.save()
                        notify_client_mass_problem(task, problem)
                    message_to_admins('⛔️ Обнаружена массовая проблема!')

    def check_new_task(self, task):
        # Добавляем новые задания из интрасервиса, если они относяться к тп и открыты
        logging.debug("Adding new task...")
        if task['ExecutorGroup'] == 'Техподдержка' and task['StatusId'] == TASK_STATUSES['Открыта']:
            logging.debug(f'Search ({task["Id"]})...')
            try:
                IntraserviceTask.objects.get(id=task['Id'])
            except ObjectDoesNotExist:
                logging.debug(f'{task["Id"]}) not found! Creating...')
                IntraserviceTask.objects.create(id=task['Id'], status=task['StatusId'],
                                                is_mass=task['IsMassIncident'],
                                                edit_person=task['Creator'],
                                                priority=task['PriorityId'],
                                                executor_group=EXECUTOR_GROUP_IDS['Техподдержка'])
                logging.debug(f'{task["Id"]}) created!')
                new_task = IntraserviceTask.objects.get(id=task['Id'])
                if new_task.description != "Проверка сервиса!":
                    self.new_task_count += 1
        logging.debug(f'Try get {task["Id"]})...')

    @staticmethod
    def executor_group_check(task, db_task: IntraserviceTask):
        if task['ExecutorGroupId']:
            if task['ExecutorGroupId'] != db_task.executor_group:
                if task['ExecutorGroupId'] != EXECUTOR_GROUP_IDS['Техподдержка']:
                    logging.debug(f'{db_task} executor group updated!')
                    db_task.executor_group = task['ExecutorGroupId']
                    db_task.save()

                    # Освобождение сотрудников
                    for ex in Executor.objects.filter(intraservice_task_active=db_task):
                        logging.debug(f'{ex} task {db_task} move to other executor group!')
                        clear_executor_active_task(ex)

    @classmethod
    def pin_to_other_executor(cls, task, db_task):
        if task['ExecutorIds']:  # and not task['ParentId']:  # ToDO: Try to remove "not task['ParentId]"
            try:
                int(task['ExecutorIds'])
            except ValueError:
                pass  # Good
            else:
                if db_task.status == TASK_STATUSES['Открыта']:
                    try:
                        executor = Executor.objects.get(intraservice_user__id=task['ExecutorIds'])
                    except ObjectDoesNotExist:
                        pass
                    else:
                        db_task.postponed_type = POSTPONED_TYPE['Критическая завка']
                        db_task.postponed_executor = executor
                        db_task.save()
                elif db_task.status == TASK_STATUSES['В работе']:
                    try:  # Исполнитель назначенный на задачу
                        executor = Executor.objects.get(intraservice_user__id=int(task['ExecutorIds']))
                    except ObjectDoesNotExist:
                        pass
                    else:
                        try:  # Исполнитель у которого в исполнении находиться задача
                            active_executor = Executor.objects.get(intraservice_task_active=db_task)
                        except ObjectDoesNotExist:
                            pass
                        else:
                            if executor != active_executor:
                                # Если исполнитель сменился
                                if active_executor.status == 'Готов':
                                    pass
                                elif active_executor.status == 'Занят':
                                    update_statistic(active_executor, work_min=round(
                                        (timezone.now() - active_executor.last_status_change).seconds / 60),
                                                     cancel_task=1)
                                    active_executor.status = 'Готов'
                                    active_executor.last_status_change = timezone.now()
                                    active_executor.intraservice_task_active = None
                                    active_executor.save()
                                    bot.send_message(executor.telegram_user.user_id,
                                                     text=r.PIN_OTHER_EXECUTOR.format(
                                                         task_id=db_task.id,
                                                         task_url=api.new_api.get_task_url(db_task.id),
                                                         executor_name=executor.intraservice_user.name,
                                                         executor_url=f"tg://user?id={executor.telegram_user.user_id}"
                                                     ))
                                else:
                                    active_executor.intraservice_task_active = None
                                    active_executor.save()
                            else:
                                if executor.intraservice_task_active:
                                    if executor.intraservice_task_active != db_task:
                                        old_task = executor.intraservice_task_active
                                        executor.intraservice_task_active = db_task
                                        executor.save()
                                        db_task.long_execution_notification = timezone.now()
                                        db_task.executor_notification_count = 0
                                        db_task.admin_notification = timezone.now()
                                        db_task.admin_notification_count = 0
                                        db_task.save()
                                        old_task.postponed_type = POSTPONED_TYPE['Критическая завка']
                                        old_task.postponed_executor = executor
                                        old_task.save()
                                        api.new_api.change_task(old_task.id,
                                                                status_id=TASK_STATUSES['Отложена'],
                                                                comment='Сотрудник взял другую заявку')
                                        api.new_api.change_task(db_task.id)
                                        old_url = api.new_api.get_task_url(old_task.id)
                                        new_url = api.new_api.get_task_url(db_task.id)
                                        bot.send_message(executor.telegram_user.user_id,
                                                         text=r.CHANGE_ACTIVE_TASK.format(
                                                             old_task_id=old_task.id,
                                                             new_task_id=db_task.id,
                                                             old_url=old_url, new_url=new_url),
                                                         parse_mode='Markdown')
                                else:
                                    pin_to_task(executor, db_task)

    @classmethod
    def check_parent_task(cls, task, db_task):
        # Проверка прикрепления заявки к родительской
        if task['ParentId']:
            parent_task = None
            try:
                parent_task = IntraserviceTask.objects.get(id=task['ParentId'])
            except ObjectDoesNotExist:
                try:
                    parent_task_json = api.new_api.get_task(task['ParentId'])
                    parent_task = IntraserviceTask.objects.create(
                        id=parent_task_json['Id'],
                        status=parent_task_json['StatusId'],
                        priority=parent_task_json['PriorityId']
                    )
                except APIError as e:
                    print(e)  # ToDo
            if parent_task:
                db_task.parent = parent_task
                db_task.save()

            try:
                active_executor = Executor.objects.get(intraservice_task_active=db_task)
            except ObjectDoesNotExist:
                pass
            else:
                if active_executor.status == 'Занят':
                    update_statistic(active_executor, work_min=round(
                        (timezone.now() - active_executor.last_status_change).seconds / 60),
                                     cancel_task=1)
                    active_executor.status = 'Готов'
                    active_executor.last_status_change = timezone.now()
                    active_executor.intraservice_task_active = None
                    active_executor.save()
                    bot.send_message(active_executor.telegram_user.user_id,
                                     text=r.PIN_OTHER_TASK.format(task_id=db_task.id,
                                                                  task_url=api.new_api.get_task_url(db_task.id),
                                                                  parent_task_id=parent_task.id,
                                                                  parent_task_url=api.new_api.get_task_url(
                                                                      parent_task.id
                                                                  ))
                                     )
                elif active_executor.status == 'Не готов':
                    update_statistic(active_executor, cancel_task=1)
                    active_executor.intraservice_active_task = None
                    active_executor.save()

    @classmethod
    def check_delete_executor_from_task(cls, task, db_task):
        try:
            executor = Executor.objects.get(intraservice_task_active=db_task)
        except ObjectDoesNotExist:
            return
        if not task['ExecutorIds']:
            # bot.send_message(executor.telegram_user.user_id, 'line ~358') ToDo
            executor.intraservice_task_active = None
            executor.save()
            if db_task.postponed_executor == executor:
                db_task.postponed_executor = None
                db_task.postponed_type = 0
                db_task.save()

    def processing_update(self, task):
        logging.debug(f'Processing task from intraservice({task["Id"]})...')

        self.check_new_task(task)

        try:
            db_task = IntraserviceTask.objects.get(id=task['Id'])
        except ObjectDoesNotExist:
            logging.debug(f'({task["Id"]}) not found! Skipped!')
            return
        else:
            logging.debug(f'{db_task} founded!')

        # Оповещение об изменении статуса
        logging.debug('Notify client...')
        if db_task.status != task['StatusId']:
            db_task.status = task['StatusId']
            logging.debug(f'{db_task} status changed!')
            if db_task.telegram_client:
                editor = api.get_status_editor(db_task, task['StatusId'])
                if editor:
                    logging.debug(f'Notify {db_task.telegram_client.telegram_user} about {db_task}...')
                    try:
                        db_task.edit_person = editor
                        if db_task.status == TASK_STATUSES['Выполнена']:
                            bot.send_message(db_task.telegram_client.telegram_user.user_id,
                                             db_task.new_status_message + f"\n{r.TASK_REVIEW}",
                                             reply_markup=kb.review_keyboard(db_task),
                                             parse_mode='Markdown')
                        else:
                            bot.send_message(db_task.telegram_client.telegram_user.user_id,
                                             db_task.new_status_message, parse_mode='Markdown')
                    except telebot.apihelper.ApiException:
                        logging.debug(f"Can't send message to {db_task.telegram_client.telegram_user}!")
            db_task.save()

        self.check_delete_executor_from_task(task, db_task)

        self.executor_group_check(task, db_task)

        self.pin_to_other_executor(task, db_task)  # ToDo: check

        self.check_parent_task(task, db_task)

    @staticmethod
    def check_tasks_in_db():
        for task in get_opened_tasks():
            try:
                api.get_task(task)
            except APIError:
                task.delete()

    def run(self):
        logging.info("Start status listener thread")
        self.check_tasks_in_db()
        pool = ThreadPool(5)
        last_update = timezone.now() - timedelta(hours=6)
        new_update = None
        self.update_enable.set()
        while self.run_enabled:
            self.new_task_count = 0
            logging.debug('Enabled creating tasks!')
            self.create_task_enable.set()
            if new_update:
                time.sleep(max(0, UPDATE_TIME - (new_update - last_update).seconds))
            else:
                time.sleep(UPDATE_TIME)
            self.update_enable.wait(UPDATE_TIME)
            logging.debug('Disabled creating tasks!')
            self.create_task_enable.clear()

            new_update = timezone.now()

            # получаем все изменения заданий
            logging.info('Get updates...')
            try:
                tasks_updates = api.get_tasks(last_update)
            except api.new_api.APIError as e:
                logging.error(e)
                tasks_updates = []
                updated = False
            else:
                updated = True
                logging.debug('Updates received!')

            # обработка обновлений
            for task in tasks_updates:
                self.processing_update(task)

            # проверка всех заданий
            logging.debug('Start sync tasks from db...')
            start_time = time.time()
            pool.map(self.task_sync, list(IntraserviceTask.objects.filter(~Q(status=29))))

            logging.debug('Finish sync tasks from db! (' + str(time.time() - start_time) + ' seconds)')

            # Смена статуса у подзадач
            for mass_task in IntraserviceTask.objects.filter(~Q(parent_id=None)):
                for task in IntraserviceTask.objects.filter(parent_id=mass_task):
                    if task.status != mass_task.status:
                        logging.debug("Sync status of children {task}!")
                        api.new_api.change_task(task.id, status_id=mass_task.status,
                                                comment='Синхронизация статуса с родителем.')

            # Удаляем сотрудников, у открытых заданий, которые были отложены
            for task in IntraserviceTask.objects.filter(status=TASK_STATUSES['Открыта']).filter(
                    postponed_type=POSTPONED_TYPE['Отложена сотрудником']):
                remove_executor(task)

            # Проверяем сотрудников, которые отложили задания
            for ex in Executor.objects.filter(
                    intraservice_task_active__status=TASK_STATUSES["Отложена"]):
                task_delay(ex)

            # Освобождаем работников, от решенных задач
            for ex in Executor.objects.filter(Q(intraservice_task_active__status=TASK_STATUSES['Выполнена']) | Q(
                    intraservice_task_active__status=TASK_STATUSES['Отменена'])):
                close_task(ex)

            # Удаляем закрытые и отмененные задания
            for task in IntraserviceTask.objects.filter(  # type: IntraserviceTask
                            Q(status=TASK_STATUSES['Закрыта']) | Q(status=TASK_STATUSES['Отменена'])):
                if not list(IntraserviceTask.objects.filter(parent=task)):
                    task.delete()

            # Освобождаем работников, у которых удалены задачи
            for ex in Executor.objects.filter(intraservice_task_active=None).filter(status='Занят'):
                close_task(ex)

            # Оповещения о долгом выполнении
            for task in IntraserviceTask.objects.filter(~Q(executor=None) & Q(executor__status='Занят')):
                executor = Executor.objects.get(intraservice_task_active=task)
                task_url = api.new_api.get_task_url(task.id)
                if (timezone.now() - task.long_execution_notification).seconds > 60 * NOTIFY_TASK_MIN:
                    bot.send_message(executor.telegram_user.user_id,
                                     text=r.LONG_WORK_EXECUTOR_NOTIFICATION.format(
                                         task_id=task.id, task_url=task_url,
                                         NOTIFY_TASK_MIN=NOTIFY_TASK_MIN * (task.executor_notification_count + 1)),
                                     parse_mode='Markdown')
                    task.executor_notification_count += 1
                    task.long_execution_notification = timezone.now()
                if (timezone.now() - task.admin_notification).seconds > 60 * MAX_TASK_MIN:
                    message_to_admins(
                        r.LONG_WORK_ADMIN_NOTIFICATION.format(
                            executor=executor.intraservice_user.name, task_id=task.id,
                            task_url=task_url, MAX_TASK_MIN=MAX_TASK_MIN * (task.admin_notification_count + 1),
                            uid=executor.telegram_user.user_id))
                    task.admin_notification_count += 1
                    task.admin_notification = timezone.now()
                task.save()

            self.postponed_notify()

            # Объединяем похожие заявки от одного пользователя
            for task in IntraserviceTask.objects.filter(~Q(telegram_client=None)).filter(parent_id=None).filter(
                    created__gte=last_update):  # type: IntraserviceTask
                try:
                    client = Client.objects.get(intraservicetask=task)  # type: Client
                except ObjectDoesNotExist:
                    continue
                for c_task in IntraserviceTask.objects.filter(telegram_client=client).filter(
                        created__gte=(timezone.now() - timedelta(minutes=60))).filter(
                        ~Q(description=None)).filter(parent_id=None):  # type: IntraserviceTask
                    if task.id == c_task.id:
                        continue
                    for problem in MASS_PROBLEMS:  # type: IntraserviceTask
                        if problem in task.description and problem in c_task.description:
                            logging.debug(
                                f'Making {c_task} parent to {task}...')
                            task.parent_id = c_task
                            api.new_api.change_task(task.id, parent_id=c_task.id)
                            task.save()
                            break

            self.group_mass_tasks()

            # Возвращаем заявки исполнителю
            for ex in Executor.objects.filter(~Q(intraservice_task_active=None)).filter(status='Готов').filter(
                    last_status_change__lte=(timezone.now() - timedelta(seconds=SEC_TO_PIN))).filter(
                    intraservice_task_active__parent__id=None).filter(
                    intraservice_task_active__executor_group=EXECUTOR_GROUP_IDS['Техподдержка']):
                re_pin_to_task(ex)

            # Новые заявки и нет сотрудников
            if len(get_ready_executors()) == 0 and self.new_task_count:
                message_to_admins(r.NEW_TASK_NO_EXECUTORS)

            # Возвращаем отложеные (из-за критической заявки) заявки исполнителю (Критические)
            for task in IntraserviceTask.objects.filter(postponed_type=POSTPONED_TYPE['Критическая завка']).filter(
                    priority=PRIORITY_STATUSES['Критический']).filter(parent_id=None).filter(
                    executor_group=EXECUTOR_GROUP_IDS['Техподдержка']).filter():
                if task.postponed_executor.intraservice_task_active:
                    if task.postponed_executor.intraservice_task_active.priority != PRIORITY_STATUSES[
                        'Критический'] and task.postponed_executor.intraservice_task_active.postponed_type == \
                            POSTPONED_TYPE['Критическая завка']:
                        pin_critical_task(task.postponed_executor, task)
                else:
                    pin_to_task_after_critical(task)

            self.pin_critical_tasks()

            # Возвращаем отложеные (из-за критической заявки) заявки исполнителю
            for task in IntraserviceTask.objects.filter(postponed_type=POSTPONED_TYPE['Критическая завка']).filter(
                    postponed_executor__status='Готов').filter(parent_id=None).filter(
                    executor_group=EXECUTOR_GROUP_IDS['Техподдержка']).filter(
                    ~Q(status=TASK_STATUSES['Закрыта']) & ~Q(status=TASK_STATUSES["Выполнена"])):
                pin_to_task_after_critical(task)

            self.pin_non_critical_tasks()

            self.blockage_notify()

            if updated:
                last_update = new_update
        pool.close()


def message_to_admins(msg):
    for admin in ADMINS_FOR_NOTIFICATION:
        try:
            user = TelegramUser.objects.get(username=admin)
        except ObjectDoesNotExist:
            continue
        try:
            bot.send_message(user.user_id, text=msg, parse_mode='Markdown')
        except telebot.apihelper.ApiException:
            continue


def pin_to_task(executor: Executor, task: IntraserviceTask):
    add_journal_record(executor)
    update_statistic(executor, ready_min=round((timezone.now() - executor.last_status_change).seconds / 60))
    executor.intraservice_task_active = task
    executor.status = 'Занят'
    executor.last_status_change = timezone.now()
    executor.save()
    task.long_execution_notification = timezone.now()
    task.executor_notification_count = 0
    task.admin_notification = timezone.now()
    task.admin_notification_count = 0
    task.save()
    api.update_executor_and_status(task.id, executor.intraservice_user.id, TASK_STATUSES['В процессе'])
    task_url = api.new_api.get_task_url(task.id)
    bot.send_message(executor.telegram_user.user_id,
                     text=r.EXECUTOR_PIN.format(task_id=task.id, task_url=task_url,
                                                priority=PRIORITY_STATUSES_R[task.priority],
                                                open_tasks=len(get_opened_tasks()),
                                                mass_tasks=len(get_mass_tasks())),
                     parse_mode='Markdown')


def pin_to_task_after_critical(task: IntraserviceTask):
    pin_to_task(task.postponed_executor, task)
    task.postponed_type = POSTPONED_TYPE['Неизвестно']
    task.postponed_executor = None
    task.save()


def re_pin_to_task(executor: Executor):
    add_journal_record(executor)
    update_statistic(executor, ready_min=round((timezone.now() - executor.last_status_change).seconds / 60))
    executor.status = 'Занят'
    executor.last_status_change = timezone.now()
    executor.save()
    executor.intraservice_task_active.long_execution_notification = timezone.now()
    executor.intraservice_task_active.executor_notification_count = 0
    executor.intraservice_task_active.admin_notification = timezone.now()
    executor.intraservice_task_active.admin_notification_count = 0
    executor.intraservice_task_active.save()
    task_url = api.new_api.get_task_url(executor.intraservice_task_active.id)
    bot.send_message(executor.telegram_user.user_id,
                     text=r.EXECUTOR_HAVE_TASK.format(task_id=executor.intraservice_task_active.id,
                                                      task_url=task_url,
                                                      open_tasks=len(get_opened_tasks())),
                     parse_mode='Markdown')


def pin_critical_task(executor: Executor, new_task: IntraserviceTask):
    old_task = executor.intraservice_task_active
    executor.intraservice_task_active = new_task
    executor.save()
    new_task.long_execution_notification = timezone.now()
    new_task.executor_notification_count = 0
    new_task.admin_notification = timezone.now()
    new_task.admin_notification_count = 0
    new_task.save()
    old_task.postponed_type = POSTPONED_TYPE['Критическая завка']
    old_task.postponed_executor = executor
    old_task.save()
    api.new_api.change_task(old_task.id, status_id=TASK_STATUSES['Отложена'], comment='Переведен на критическую заявку')
    api.new_api.change_task(new_task.id, status_id=TASK_STATUSES['В работе'],
                            executor_ids=[executor.intraservice_user.id])
    old_url = api.new_api.get_task_url(old_task.id)
    new_url = api.new_api.get_task_url(new_task.id)
    bot.send_message(executor.telegram_user.user_id,
                     text=r.CHANGE_TO_CRITICAL_MESSAGE.format(old_task_id=old_task.id, new_task_id=new_task.id,
                                                              old_url=old_url, new_url=new_url,
                                                              executors=len(get_ready_executors()),
                                                              open_tasks=len(get_opened_tasks()),
                                                              mass_tasks=len(get_mass_tasks())),
                     parse_mode='Markdown')


def task_delay(executor):
    task = executor.intraservice_task_active
    task.postponed_type = POSTPONED_TYPE['Отложена сотрудником']
    task.postponed_executor = executor
    task.save()
    update_statistic(executor, postponed_task=1,
                     work_min=round((timezone.now() - executor.last_status_change).seconds / 60))
    executor.status = 'Готов'
    executor.last_status_change = timezone.now()
    executor.intraservice_task_active = None
    executor.save()
    bot.send_message(executor.telegram_user.user_id,
                     text=r.EXECUTOR_FREE)


def close_task_after_mass(executor: Executor):
    if executor.status == 'Занят':
        add_journal_record(executor)
        update_statistic(executor, work_min=round((timezone.now() - executor.last_status_change).seconds / 60),
                         cancel_task=1)
        task = executor.intraservice_task_active
        task_url = api.new_api.get_task_url(task.id)
        executor.intraservice_task_active = None
        executor.status = 'Готов'
        executor.last_status_change = timezone.now()
        executor.save()
        bot.send_message(executor.telegram_user.user_id,
                         text=r.CHANGE_FROM_MASS_TASK.format(task_id=task.id, task_url=task_url))
    elif executor.status == 'Не готов':
        update_statistic(executor, cancel_task=1)
        executor.intraservice_task_active = None
        executor.save()


def close_task(executor: Executor):
    if executor.status == 'Занят':
        add_journal_record(executor)
        update_statistic(executor, work_min=round((timezone.now() - executor.last_status_change).seconds / 60),
                         done_task=1)
        executor.status = 'Готов'
        executor.last_status_change = timezone.now()
        executor.intraservice_task_active = None
        executor.save()
        bot.send_message(executor.telegram_user.user_id,
                         text=r.EXECUTOR_FREE)
    elif executor.status == 'Не готов':
        update_statistic(executor, done_task=1)
        executor.intraservice_task_active = None
        executor.save()


def remove_executor(task: IntraserviceTask):
    api.new_api.change_task(task.id, executor_ids=[])


def clear_executor_active_task(executor: Executor):
    add_journal_record(executor)
    update_statistic(executor, work_min=round((timezone.now() - executor.last_status_change).seconds / 60))
    executor.intraservice_task_active = None
    executor.status = 'Готов'
    executor.last_status_change = timezone.now()
    executor.save()
    bot.send_message(executor.telegram_user.user_id,
                     text=r.EXECUTOR_FREE)


def notify_client_mass_problem(task: IntraserviceTask, problem: str):
    if task.telegram_client:
        try:
            bot.send_message(task.telegram_client.telegram_user.user_id,
                             r.NOTIFY_CLIENT_MASS_PROBLEM.format(type=problem))
        except telebot.apihelper.ApiException:
            pass
