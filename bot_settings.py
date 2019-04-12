from enum import Enum

BOT_TOKEN = ""  # Токен бота

# Настройки бд
DB_USER = ""
DB_PASSWORD = ""
DB_HOST = ""
DB_NAME = ""
DB_PORT = ""


USE_PROXIES = False
PROXIES = {
    'http': '',
    'https': ''
}


class TaskStatus(Enum):
    CANCEL_BY_USER = "Cancel by user"
    SENDING_TO_API = "Task sending to api and wait for response"
    IN_API = "In API"


class TaskStep(Enum):
    WAIT_FOR_BRAND = "Wait for brand"
    WAIT_FOR_SHOP_FULLNAME = "Wait for fullname"
    WAIT_FOR_MOBILE_NUMBER = "Wait for mobile number"
    WAIT_FOR_TEAM_VIEWER = "Wait for team viewer"
    WAIT_FOR_SERVICE = "Wait for service"
    WAIT_FOR_DESCRIPTION = "Wait for description"
    WAIT_FOR_KKM_NUMBER = "Wait for kkm number"
    WAIT_FOR_BLOCK = "Wait for block"
    WAIT_FOR_SCREENSHOT = "Wait for screenshot"
    FILLED = "Filled"


Priorities = [
    {11: 'Низкий'},
    {9: 'Средний'},
    {10: 'Высокий'},
    {12: 'Критический'}]

# Настройки интрасервиса
API_LOGIN = ""
API_PASSWORD = ""
SERVER_URL = ''

EVALUATIONS = {
    "Отлично": 4,
    "Хорошо": 2,
    "Удовлетворительно": 3,
    "Плохо": 1,
}

MASS_PROBLEMS_PRIORITY = {
    'Не работает интернет или телефония': "Высокий",
    'Неисправность ФР': "Критический",
    'Проблемы связанные с 1С': "Критический",
    'Заказ клиента OMNI': "Низкий",
    'Проблемы с Закрытием смены': "Высокий",
    'Компьютерное оборудование(сканер\принтер)': "Средний",
    'Не запускается ПК': "Высокий"
}

MASS_PROBLEMS_SERVICE_IDS = {
    'Не работает интернет или телефония': 26,
    'Неисправность ФР': 536,
    'Проблемы связанные с 1С': 595,
    'Заказ клиента OMNI': 421,
    'Проблемы с Закрытием смены': 19,
    'Компьютерное оборудование(сканер\принтер)': 127,
    'Не запускается ПК': 589
}

MASS_PROBLEMS_TASK_TYPE_ID = {
    'Не работает интернет или телефония': 1,
    'Неисправность ФР': 1009,
    'Проблемы связанные с 1С': 1,
    'Заказ клиента OMNI': 1,
    'Проблемы с Закрытием смены': 1,
    'Компьютерное оборудование(сканер\принтер)': 30,
    'Не запускается ПК': 1003
}

MASS_PROBLEMS = [x[0] for x in MASS_PROBLEMS_PRIORITY.items()]


ADMINS_FOR_NOTIFICATION = ADMINS_TELEGRAM_UNAME = ("KuRBeZz", "ITHELPIRG", )  # список людей, которым будут приходить уведомления
UPDATE_TIME = 15  # Раз в какое кол-во секунд бот будет запрашивать обновления от API IntraService
NOTIFY_TASK_MIN = 25  # Через сколько минут будет приходить уведомление работнику ТП
MAX_TASK_MIN = 25  # Через сколько минут будет приходить уведомление админу о долгом выполнении задания
SEC_TO_PIN = 30  # Через сколько секунд будет выдача заданий
