import logging
from logging.handlers import RotatingFileHandler

import requests
import threading
import time
from typing import List
from django.core.files.base import ContentFile
from django.core.exceptions import *
from django.utils import timezone
from bot_settings import BOT_TOKEN, TaskStep, ADMINS_TELEGRAM_UNAME, MASS_PROBLEMS, MASS_PROBLEMS_PRIORITY, USE_PROXIES, PROXIES
import responses as r
import keyboards as kb
import telebot
from telebot import types, apihelper
import re
from api_helper import Api
import zipfile

import os
import responses
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()

from data.models import *

from listener import TaskListener, message_to_admins
from statistics import update_statistic
from journal import add_journal_record
from executor import get_ready_executors, get_working_executors
from task import get_mass_tasks, get_opened_tasks


if USE_PROXIES:
    apihelper.proxy = PROXIES


logging.basicConfig(
    handlers=[RotatingFileHandler('./logs/bot.log', mode='a', maxBytes=25 * 1024 * 1024)]
)

api = Api()
bot = telebot.TeleBot(token=BOT_TOKEN)

task_creating_lock = threading.Lock()


# noinspection PyProtectedMember
def register_handlers():
    bot.add_message_handler(bot._build_handler_dict(executor_ready, commands=['ready']))
    bot.add_message_handler(bot._build_handler_dict(executor_stop, commands=['stop']))
    bot.add_message_handler(bot._build_handler_dict(info_message, commands=["message"]))
    bot.add_message_handler(bot._build_handler_dict(info, commands=["info"]))
    # bot.add_message_handler(bot._build_handler_dict(get_test_result, commands=['test_results']))
    bot.add_message_handler(bot._build_handler_dict(help_message, commands=['help']))
    # bot.add_message_handler(bot._build_handler_dict(contact_message, content_types=['contact']))
    bot.add_message_handler(bot._build_handler_dict(start_handler, commands=["start"]))
    bot.add_message_handler(bot._build_handler_dict(instructions, func=lambda msg: msg.text == r.INSTRUCTIONS))
    bot.add_message_handler(bot._build_handler_dict(cancel_make_task, func=lambda msg: msg.text == r.CANCEL_MAKE_TASK))
    bot.add_message_handler(bot._build_handler_dict(make_task, func=lambda msg: msg.text == r.MAKE_TASK))
    bot.add_message_handler(bot._build_handler_dict(ping, commands=["ping"]))
    bot.add_message_handler(bot._build_handler_dict(cancel_make_task, commands=["cancel"]))
    bot.add_message_handler(bot._build_handler_dict(get_client, commands=["client"]))
    bot.add_message_handler(bot._build_handler_dict(get_statistic, commands=['statistic']))
    bot.add_message_handler(bot._build_handler_dict(steps_handler, content_types=['text', 'photo']))
    bot.add_callback_query_handler(bot._build_handler_dict(task_review,
                                                           func=lambda call: re.search(
                                                               r'^(Отлично|Хорошо|Удовлетворительно|Плохо),[\d]+$',
                                                               call.data) is not None))


def instructions(message: types.Message):
    bot.send_message(message.chat.id, "Инструкции")


def add_filled_task():
    logging.debug("Add filled task...")
    stat = Statistic.objects.get_or_create(name="filled")[0]
    stat.count += 1
    stat.save()
    logging.debug("Filled task added!")


def add_created_task():
    logging.debug("Add created task...")
    stat = Statistic.objects.get_or_create(name="created")[0]
    stat.count += 1
    stat.save()
    logging.debug("Created task added!")


def add_success_task():
    logging.debug("Add success task...")
    stat = Statistic.objects.get_or_create(name="success")[0]
    stat.count += 1
    stat.save()
    logging.debug("Success task added!")


def get_screenshot(file_id):
    path = bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{path.file_path}"
    response = requests.get(url)
    return response.content


# Bot functions
def executor_ready(message):
    try:
        executor = Executor.objects.get(telegram_user__user_id=message.from_user.id)
    except ObjectDoesNotExist:
        bot.send_message(message.from_user.id, 'Вы не являетесь работником ТП.')
        return
    if executor.status == 'Не готов':
        logging.debug(f'Change status of {executor} to (Ready)!')
        executor.status = 'Готов'
        executor.last_status_change = timezone.now()
        executor.save()
        bot.send_message(executor.telegram_user.user_id,
                         text=r.EXECUTOR_READY.format(executors_ready=len(get_ready_executors())))
    elif executor.status == 'Готов':
        bot.send_message(executor.telegram_user.user_id,
                         text=r.EXECUTOR_READY.format(executors_ready=len(get_ready_executors())))
    elif executor.status == 'Занят':
        task = executor.intraservice_task_active
        task_url = api.new_api.get_task_url(task.id)
        bot.send_message(message.from_user.id,
                         text=r.EXECUTOR_HAVE_TASK.format(task_id=task.id, task_url=task_url,
                                                          open_tasks=len(get_ready_executors())),
                         parse_mode='Markdown')


def executor_stop(message):
    try:
        executor = Executor.objects.get(telegram_user__user_id=message.from_user.id)
    except ObjectDoesNotExist:
        bot.send_message(message.from_user.id, 'Вы не являетесь сотрудником ТП.')
        return
    if executor.status == 'Готов':
        add_journal_record(executor)
        update_statistic(executor, ready_min=round((timezone.now() - executor.last_status_change).seconds / 60))
        executor.status = 'Не готов'
        executor.last_status_change = timezone.now()
        executor.save()
        bot.send_message(message.from_user.id,
                         text=r.EXECUTOR_STOP)
    elif executor.status == 'Занят':
        add_journal_record(executor)
        update_statistic(executor, work_min=round((timezone.now() - executor.last_status_change).seconds / 60))
        executor.status = 'Не готов'
        executor.last_status_change = timezone.now()
        executor.save()
        bot.send_message(message.from_user.id,
                         text=r.EXECUTOR_STOP_WITH_TASK)
    elif executor.status == 'Не готов':
        bot.send_message(message.from_user.id, 'Вы не начинали работу.')


def is_executor(user: types.User):
    try:
        Executor.objects.get(telegram_user__user_id=user.id)
    except ObjectDoesNotExist:
        return False
    return True


def is_admin(user: types.User):
    if user.username in ADMINS_TELEGRAM_UNAME:
        return True
    return False


def is_collaborator(user: types.User):
    if is_executor(user) or is_admin(user):
        return True
    return False


def info_message(message: types.Message):
    if not is_collaborator(message.from_user):
        bot.send_message(message.from_user.id, 'Вы не являетесь сотрудником.')
        return
    try:
        message_text = message.text.split('message ')[1]
    except IndexError:
        bot.send_message(message.from_user.id, 'Ошибка!')
        return
    for user in TelegramUser.objects.all():
        try:
            bot.send_message(user.user_id, message_text, parse_mode="Markdown")
        except telebot.apihelper.ApiException:
            logging.info(f"Can't send message to {user}")
    bot.reply_to(message, 'Сообщение отправлено!')


def info(msg: types.Message):
    if not is_admin(msg.from_user):
        bot.send_message(msg.from_user.id, 'Вы не являетесь админом.')
        return

    def format_executor(ex: Executor) -> str:
        return f"  [{ex.intraservice_user.name}](tg://user?id={ex.telegram_user.user_id}) \n"

    def format_task(tsk: IntraserviceTask) -> str:
        task_url = api.new_api.get_task_url(tsk.id)
        return f" [#{tsk.id}]({task_url})"

    def format_executor_with_task(ex: Executor) -> str:
        tsk = ex.intraservice_task_active
        if not tsk:
            return f"  [{ex.intraservice_user.name}](tg://user?id={ex.telegram_user.user_id})\n"
        else:
            task_url = api.new_api.get_task_url(tsk)
            return f"  [{ex.intraservice_user.name}](tg://user?id={ex.telegram_user.user_id}) " \
                f"([#{tsk.id}]({task_url})\n"

    ready_executors = get_ready_executors()
    ready_executors_list = ''
    for executor in ready_executors:
        ready_executors_list += format_executor(executor)

    working_executors = get_working_executors()
    working_executors_list = ''
    for executor in working_executors:
        working_executors_list += format_executor_with_task(executor)

    opened_tasks = get_opened_tasks()
    opened_tasks_list = ''
    for task in opened_tasks:
        opened_tasks_list += format_task(task)
    if opened_tasks:
        opened_tasks_list += '\n'

    mass_tasks = get_mass_tasks()
    mass_tasks_list = ''
    for task in mass_tasks:
        mass_tasks += format_task(task)
    if mass_tasks:
        mass_tasks_list += '\n'

    bot.send_message(
        msg.from_user.id,
        r.INFO_MESSAGE.format(
            ready_executors=f"{len(ready_executors)}:" if ready_executors else "нет",
            ready_executors_list=ready_executors_list,
            working_executors=f"{len(working_executors)}:" if working_executors else "нет",
            working_executors_list=working_executors_list,
            opened_tasks=f"{len(opened_tasks)}:" if opened_tasks else "нет",
            opened_tasks_list=opened_tasks_list,
            blockage_exist="Завал есть" if len(opened_tasks) >= 5 else "Завала нет",
            mass_tasks=f"len(mass_tasks):" if mass_tasks else "нет",
            mass_tasks_list=mass_tasks_list
        ),
        parse_mode="Markdown"
    )


def get_test_result(msg: types.Message):
    wrong_tests = IntraserviceTest.objects.filter(status=False)  # type: List[IntraserviceTest]
    if wrong_tests:
        with open('wrong_test.txt', 'w') as f:
            for t in wrong_tests:
                f.write(f'{t.date} | {t.error} \n')
        bot.send_document(msg.from_user.id, open('wrong_test.txt', 'r'))
        os.remove('./wrong_test.txt')
    else:
        bot.send_message(msg.from_user.id, 'За последние два дня небыло замечено проблем!')


def help_message(msg: types.Message):
    if is_admin(msg.from_user):
        reply_text = "/message - отправить сообщение клиентам\n" \
                     "/info - узнать положение дел\n" \
                     "/test_results - результаты тестирования"
    elif is_executor(msg.from_user):
        reply_text = "/ready - начать работу\n" \
                     "/stop - завершить работу\n" \
                     "/message - отправить сообщение клиентам\n"
    else:
        reply_text = "/start - создание заявок"
    bot.send_message(msg.from_user.id, reply_text)


def contact_message(message: types.Message):
    try:
        user = TelegramUser.objects.get(user_id=message.from_user.id)
    except ObjectDoesNotExist:
        return
    user.telephone = message.contact.phone_number
    user.save()


# Start command handler
def start_handler(message: types.Message):
    user = TelegramUser.objects.get_or_create(user_id=message.from_user.id)[0]
    client = Client.objects.get_or_create(telegram_user=user)[0]
    if message.from_user.username:
        user.username = message.from_user.username
    user.save()
    bot.send_message(message.chat.id, r.START, reply_markup=kb.start())


# Cancel make task handler
def cancel_make_task(message):
    start_handler(message)


def make_task(message):
    bot.send_message(message.chat.id, responses.CHOICE_BRAND, reply_markup=kb.brands_keyboard())
    user = TelegramUser.objects.get(user_id=message.chat.id)
    client = Client.objects.get(telegram_user=user)
    task = TelegramTask.objects.create(current_step=TaskStep.WAIT_FOR_BRAND.value)
    task.save()
    client.telegram_task = task
    client.save()


def ping(message):
    bot.send_message(message.chat.id, "Я жив :)", reply_markup=kb.start_keyboard())


def cancel_make_task_by_command(message):
    cancel_make_task(message)


def get_client(message):
    try:
        executor = Executor.objects.get(telegram_user__user_id=message.from_user.id)
    except ObjectDoesNotExist:
        bot.send_message(message.from_user.id, 'Вы не являетесь сотрудником ТП.')
        return
    task_id = message.text.split(' ')[1] if len(message.text.split(' ')) == 2 else None
    if task_id:
        try:
            task_id = int(task_id)
        except ValueError:
            bot.send_message(message.from_user.id, 'Ошибка ввода номера заявки!')
            return
        try:
            task = IntraserviceTask.objects.get(id=task_id)
        except ObjectDoesNotExist:
            bot.send_message(message.from_user.id, 'Заявка не найдена!')
            return
        if task.telegram_client:
            bot.send_message(message.from_user.id,
                             text='[Клиент](tg://user?id={uid}) по [заявке #{task_id}]({task_url})'.format(
                                 uid=task.telegram_client.telegram_user.user_id,
                                 task_id=task.id, task_url=api.new_api.get_task_url(task.id)),
                             parse_mode='Markdown')
        else:
            bot.send_message(message.from_user.id, 'Заявка создана через интрасервис!')
    else:
        if executor.intraservice_task_active.telegram_client:
            task = executor.intraservice_task_active
            task_url = api.new_api.get_task_url(task.id)
            bot.send_message(message.from_user.id,
                             text='[Клиент](tg://user?id={uid}) по [заявке #{task_id}]({task_url})'.format(
                                 uid=task.telegram_client.telegram_user.user_id,
                                 task_id=task.id, task_url=task_url),
                             parse_mode='Markdown')
        else:
            bot.send_message(message.from_user.id, 'Заявка создана через интрасервис!')


def get_statistic(message):
    if message.from_user.username not in ADMINS_TELEGRAM_UNAME:
        bot.send_message(message.from_user.id, 'Вы не являетесь админом!')
        return

    with open('blockage.txt', 'w', encoding='utf-8') as f:
        f.write(f'{"Начало завала":17} | {"Конец завала":17}\n')
        for j in BlockageJournal.objects.all():
            f.write(f'{j.from_time.strftime("%d.%m.%y %H:%M:%S"):17} | {j.to_time.strftime("%d.%m.%y %H:%M:%S"):17}\n')
    bot.send_document(message.from_user.id, open('blockage.txt', 'rb'), caption='Завалы')

    with open('statistic.txt', 'w', encoding='utf-8') as f:
        f.write(f'{u"Сотрудник":31} | {u"Дата":10} | {u"Время ожидания":14} | {u"Время работы":13} '
                f'| {u"Выполненые заявки":17} | {u"Массовые заявки":15} | {u"Отложеные заявки":15}\n')
        for st in ExecutorStatistics.objects.all():
            f.write(
                f'{st.executor.intraservice_user.name:31} | {str(st.date):10} | {st.ready_min:14} | {st.work_min:13} '
                f'| {st.done_tasks:17} | {st.mass_tasks:15} | {st.postponed_tasks:15}\n')
    bot.send_document(message.from_user.id, open('statistic.txt', 'rb'), caption='Статистика сотрудников')

    with open('journal.txt', 'w', encoding='utf-8') as f:
        f.write(f'{u"Сотрудник":35} | {u"Статус":6} | {u"Начало":17} | {u"Конец":17}\n')
        for j in Journal.objects.all():
            f.write(f'{j.executor.intraservice_user.name:35} | {j.status:6} '
                    f'| {str(j.from_time.strftime("%y-%m-%d %H:%M:%S")):17} '
                    f'| {str(j.to_time.strftime("%y-%m-%d %H:%M:%S")):17}\n')
    bot.send_document(message.from_user.id, open('journal.txt', 'rb'), caption='Смены статусов сотрудников')


def steps_handler(message):
    try:
        task = TelegramTask.objects.get(client__telegram_user__user_id=message.from_user.id)
    except ObjectDoesNotExist:
        start_handler(message)
        return
    if TaskStep(task.current_step) == TaskStep.WAIT_FOR_BRAND:  # get position
        if message.text in r.BRANDS:
            task.brand = message.text
            # task.priority = PRIORITY_STATUSES[[x[1] for x in r.USER_POSITIONS if x[0] == message.text][0]]
            task.current_step = TaskStep.WAIT_FOR_SHOP_FULLNAME.value
            task.save()
            add_created_task()
            bot.send_message(message.chat.id, r.ENTER_SHOP_FULLNAME, reply_markup=kb.cancel_keyboard())
        else:
            bot.send_message(message.chat.id, r.CHOICE_BRAND, reply_markup=kb.brands_keyboard())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_SHOP_FULLNAME:
        task.shop_fullname = message.text
        task.current_step = TaskStep.WAIT_FOR_MOBILE_NUMBER.value
        task.save()
        bot.send_message(message.chat.id, r.MOBILE_NUMBER_SELECT, reply_markup=kb.cancel_keyboard())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_MOBILE_NUMBER:
        if len(message.text) < 4:
            bot.send_message(message.chat.id, r.MOBILE_NUMBER_SELECT_ERROR, reply_markup=kb.remove_keyboard())
        else:
            task.mobile_number = message.text
            task.current_step = TaskStep.WAIT_FOR_SERVICE.value
            task.save()
            bot.send_message(message.chat.id, r.TASK_DESCRIPTION_SELECT, reply_markup=kb.mass_problems())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_SERVICE:
        description = message.text
        try:
            if description in MASS_PROBLEMS:
                task.description = description
                if task.description == 'Неисправность ФР':
                    task.current_step = TaskStep.WAIT_FOR_KKM_NUMBER.value
                    task.save()
                    bot.send_message(message.chat.id, r.ENTER_KKM_NUMBER, reply_markup=kb.cancel_keyboard())
                else:
                    task.current_step = TaskStep.WAIT_FOR_DESCRIPTION.value
                    task.save()
                    bot.send_message(message.chat.id, r.ENTER_ENTER_TRUE_DESCRIPTION, reply_markup=kb.cancel_keyboard())
            else:
                bot.send_message(message.chat.id, r.TASK_DESCRIPTION_SELECT_ERROR, reply_markup=kb.mass_problems())
        except Exception as e:
            logging.warning(e)
            bot.send_message(message.chat.id, r.TASK_DESCRIPTION_SELECT_ERROR, reply_markup=kb.remove_keyboard())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_KKM_NUMBER:
        task.kkm_number = message.text
        task.current_step = TaskStep.WAIT_FOR_DESCRIPTION.value
        task.save()
        bot.send_message(message.chat.id, r.ENTER_ENTER_TRUE_DESCRIPTION, reply_markup=kb.cancel_keyboard())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_DESCRIPTION:
        task.true_description = message.text
        task.current_step = TaskStep.WAIT_FOR_TEAM_VIEWER.value
        task.save()
        bot.send_message(message.chat.id, r.ENTER_TEAM_VIEWER, reply_markup=kb.skip_and_cancel_keyboard())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_TEAM_VIEWER:
        if message.text != r.SKIP_BUTTON:
            task.team_viewer = message.text
        task.current_step = TaskStep.WAIT_FOR_BLOCK.value
        task.save()
        bot.send_message(message.chat.id, r.ENTER_IS_BLOCK, reply_markup=kb.block_keyboard())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_BLOCK:
        if message.text in [r.ENTER_IS_BLOCK_YES, r.ENTER_IS_BLOCK_NO]:
            task.block_work = message.text == r.ENTER_IS_BLOCK_YES

            if task.block_work:
                task.priority = PRIORITY_STATUSES["Критический"]
            else:
                if task.description in MASS_PROBLEMS:
                    task.priority = PRIORITY_STATUSES[MASS_PROBLEMS_PRIORITY[task.description]]
                else:
                    task.priority = PRIORITY_STATUSES["Низкий"]
            task.current_step = TaskStep.WAIT_FOR_SCREENSHOT.value
            task.save()
            bot.send_message(message.chat.id, r.SCREENSHOT_ATTACH_ASK, reply_markup=kb.screenshot_ask_keyboard())
        else:
            bot.send_message(message.chat.id, r.ENTER_IS_BLOCK, reply_markup=kb.block_keyboard())
    elif TaskStep(task.current_step) == TaskStep.WAIT_FOR_SCREENSHOT:
        if message.text == r.SCREENSHOT_ATTACH_YES:
            bot.send_message(message.chat.id, r.SCREENSHOT_ATTACH_CALL, reply_markup=kb.screenshot_wait_keyboard())
        elif message.text == r.SCREENSHOT_ATTACH_CANCEL or message.text == r.SCREENSHOT_ATTACH_NO:
            task.current_step = TaskStep.FILLED.value
            task.save()
            bot.send_message(message.chat.id, r.TASK_FILLED, reply_markup=kb.remove_keyboard())
            threading.Thread(target=create_task_threaded, kwargs=({'task': task, 'message': message})).start()
            start_handler(message)
        elif message.content_type == "photo":
            task.current_step = TaskStep.FILLED.value
            screenshot = get_screenshot(message.photo[-1].file_id)
            filename = f"{message.from_user.id}_{timezone.now().strftime('%Y-%m-%dT%H:%M:%S')}.jpg"
            task.screenshot.save(filename, ContentFile(screenshot))
            task.save()
            bot.send_message(message.chat.id, r.TASK_FILLED, reply_markup=kb.remove_keyboard())
            threading.Thread(target=create_task_threaded, kwargs=({'task': task, 'message': message})).start()
            start_handler(message)


def task_review(call: types.CallbackQuery):
    rating, task_id = call.data.split(',')
    try:
        task = IntraserviceTask.objects.get(id=task_id)
    except ObjectDoesNotExist:
        task = task_id
        intra_task = api.new_api.get_task(task_id)
        last_editor = api.get_last_editor(task_id)
        msg_text = (f"Для вашей заявки *{task}* "
                    f"сотрудником *{last_editor}* "
                    f"установлен статус *{TASK_STATUSES_R[intra_task['StatusId']]}*"
                    f"\n-----\nСпасибо за оценку!\n"
                    f"Вы оценили работу тех. поддержки на *{rating}*")
    else:
        msg_text = task.new_status_message + (f"\n-----\nСпасибо за оценку!\n"
                                              f"Вы оценили работу тех. поддержки на *{rating}*")
    bot.edit_message_text(
        text=msg_text, message_id=call.message.message_id, chat_id=call.message.chat.id, parse_mode="Markdown"
    )
    api.send_task_review(task, rating)
    add_success_task()


def create_task_threaded(task: TelegramTask, message: types.Message):
    logging.debug("Creating task...")
    logging.debug("Wait creating enable...")
    task_thread.update_enable.wait(0.3)  # ToDo
    logging.debug("Disable updates...")
    task_thread.update_enable.clear()
    task_thread.new_task_count += 1
    with task_creating_lock:
        retry = 5
        logging.debug("Sending request to server...")
        while True:
            try:
                new_task = api.create_task(task)
            except api.new_api.APIError as e:
                print(e)
                retry -= 1
                if not retry:
                    bot.send_message(message.chat.id,
                                     ('Ошибка создания заявки!\n'
                                      'Позвоните на номера тех поддержки.'))
                    return
                time.sleep(5)
            else:
                logging.debug('Sending done!')
                break
        logging.debug(f"Create IntraserviceTask({new_task['Id']})...")
        try:
            intraservice_task = IntraserviceTask.objects.get(id=new_task['Id'])
        except ObjectDoesNotExist:
            logging.debug(f"Creating IntraserviceTask({new_task['Id']}): not found!")
            intraservice_task = IntraserviceTask.objects.update_or_create(
                id=new_task['Id'], status=new_task['StatusId'],
                is_mass=new_task['IsMassIncident'],
                edit_person=new_task['Creator'],
                description=new_task['Description'],
                priority=task.priority,
                executor_group=EXECUTOR_GROUP_IDS['Техподдержка'])[0]
        else:
            logging.debug(f"Creating IntraserviceTask({new_task['Id']}): found!")
            intraservice_task.is_mass = new_task['IsMassIncident']
            intraservice_task.status = new_task['StatusId']
            intraservice_task.edit_person = new_task['Creator']
            intraservice_task.description = new_task['Description']
            intraservice_task.priority = task.priority
            intraservice_task.executor_group = EXECUTOR_GROUP_IDS['Техподдержка']
            intraservice_task.save()
        task.delete()
        client = Client.objects.get(telegram_user__user_id=message.from_user.id)  # type: Client
        client.intraservicetask_set.add(intraservice_task)
        client.save()
        add_filled_task()
        logging.debug(f'Sending message to TelegramUser({message.chat.id}) after creating task...')
        try:
            bot.send_message(message.chat.id, intraservice_task.register_message, parse_mode="Markdown",
                             reply_markup=kb.remove_keyboard())
        except telebot.apihelper.ApiException:
            logging.warning(f"Can't send message to TelegramUser({message.chat.id})")
        else:
            logging.info(f'Message to TelegramUser({message.chat.id}) sended!')
        start_handler(message)
        logging.debug('Enable updates...')
        task_thread.update_enable.set()


def start_testing():
    class TestingError(Exception):
        def __init__(self, error_text):
            self.error_text = error_text

        def __bool__(self):
            return False

    with task_creating_lock:
        try:
            retry = 5
            logging.debug("Starting testing...")
            while True:
                logging.debug("Try create task...")
                try:
                    new_task = api.creating_test_task()
                except api.new_api.APIError as e:
                    try:
                        print(e)
                    except UnicodeEncodeError:
                        pass
                    retry -= 1
                    if not retry:
                        raise TestingError("Creating task error!")
                    time.sleep(5)
                else:
                    logging.debug('Task created!')
                    break

            retry = 5
            while True:
                logging.debug("Try close task...")
                try:
                    api.new_api.change_task(new_task['Id'], status_id=TASK_STATUSES['Выполнена'],
                                            reason=189, comment='Тестирование прошло успешно!')
                except api.new_api.APIError as e:
                    logging.warning(e)
                    retry -= 1
                    if not retry:
                        raise TestingError("Change task status error!")
                    time.sleep(5)
                else:
                    logging.debug('Task closed!')
                    break
        except TestingError as e:
            IntraserviceTest.objects.create(status=False, error=e.error_text)
            return e
        else:
            IntraserviceTest.objects.create(status=True)
            return True


def testing_thread():
    while True:
        if not start_testing():
            message_to_admins("Произошла ошибка при тестировании!")
        time.sleep(15 * 60)

        # remove old tests result
        IntraserviceTest.objects.filter(date__lte=timezone.now() - timezone.timedelta(days=2)).delete()


def close_with_message(task_thread_fallen=False, testing_thread_fallen=False):
    if task_thread_fallen or testing_thread_fallen:
        bot.stop_polling()
        task_thread.run_enabled = False
    elif task_thread_fallen:
        task_thread.run_enabled = False
    if not start_testing():
        message_to_admins("Произошла ошибка при тестировании!")
    logs_filenames = ["bot.log", "stdout.log", "stderr.log"]
    with zipfile.ZipFile("logs.zip", "w") as zp:
        for name in logs_filenames:
            try:
                zp.write(f"./logs/{name}")
            except FileNotFoundError:
                pass
    bot.send_document(50976308, open('logs.zip', 'rb'), caption='Бот упал!')
    task_thread.join()
    exit(-1)


task_thread = TaskListener()
task_thread.start()
logging.info("Work thread started")

register_handlers()
bot_thread = threading.Thread(target=bot.polling,
                              kwargs={'none_stop': True,
                                      'timeout': 10},
                              daemon=True)
bot_thread.start()

logging.info("Bot thread started")
# testing_th = threading.Thread(target=testing_thread, daemon=True)
# testing_th.start()
#logging.info("Testing thread stated")


if __name__ == '__main__':
    bot.delete_webhook()

    while True:
        #if not task_thread.is_alive() or not testing_th.is_alive():
        #    close_with_message(not task_thread.is_alive(), not testing_th.is_alive())
        if not bot_thread.is_alive():
            bot.stop_polling()
            time.sleep(10)
            register_handlers()
            bot_thread = threading.Thread(target=bot.polling,
                                          kwargs={'none_stop': True,
                                                  'timeout': 10},
                                          daemon=True)
            bot_thread.start()
            logging.info("Bot thread restarted")
        time.sleep(5)
