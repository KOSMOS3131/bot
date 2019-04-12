from django.db import models


PRIORITY_STATUSES = {
        "Низкий": 11,
        "Средний": 9,
        "Высокий": 10,
        "Критический": 12,
        "АРС1": 13,
        "Регламент": 16,
    }

PRIORITY_STATUSES_R = {x: y for y, x in PRIORITY_STATUSES.items()}
PRIORITY_STATUSES_DJANGO = ((x, PRIORITY_STATUSES_R[x]) for x in PRIORITY_STATUSES_R)

TASK_STATUSES = {
    "Отложена": 26,
    "В работе ": 27,
    "Закрыта": 28,
    "Выполнена": 29,
    "Отменена": 30,
    "Открыта": 31,
    "Требует уточнения": 35,
    "В процессе 2-я линия": 36,
    "В процессе 3-я линия": 37,
    "В процессе ": 38,
    "Не требует отслеживания": 39,
    "Сервис - Подлежит замене/компенсации": 40,
    "В работе(АРС)": 41,
    "Сервис - Принято (ожидает вывоза)": 42,
    "Сервис - Подлежит ремонту в местном СЦ": 43,
    "Сервис - Отправлено на склад": 44,
    "Сервис - Отправлено в Офис": 45,
    "Сервис - Оприходовано складом": 46,
    "Сервис - Получено офисом": 47,
    "Сервис - Отправлен в Авторизованный СЦ": 48,
    "Сервис - Ремонт завершен": 49,
    "Сервис - Снято с гарантии": 50,
    "Сервис - Отправлено в магазин/место хранения": 51,
    "Согласование с Ит директором": 52,
    "На согласовании с юрисконсультом": 53,
    "Согласование с руководителем": 54,
    "Согласован": 55,
    "Требуется уточнение ": 56,
    "В пути (отгружено)": 57,
    "Уценка - Зарезервировано": 58,
    "Уценка - Продано": 59,
    "Уценено ": 60,
    "Требуется уточнение": 61,
    "Отклонена": 62,
    "Готовится претензия ": 63,
    "Претензия передана на рассмотрение ": 64,
    "Определение цены и наличия товара": 65,
    "Определение стажа сотрудника": 66,
    "Ожидает рассмотрения": 67,
    "Ожидает вывоза": 68,
    "ТМЦ отправлены": 69,
    "Получено в полном объеме": 70,
    "ТМЦ получены частично": 71,
    "Согласование со складом": 72,
    "В процессе - на уточнении у пользователя": 73,
    "Подбор товара": 74,
    "Товар подобран полностью": 75,
    "Товар подобран с изменениями": 76,
    "Претензия удовлетворена": 77,
    "Претензия отклонена": 78,
    "Согласование с категорийными менеджерами": 79,
    "Согласование с финансовой дирекцией": 80,
    "Согласование": 81,
    "Сторнирование документа ": 82,
    "Ввод корректного документа": 83,
    "Выдано Заказчику": 84,
    "Возвращено в АСЦ по истечении 14 дней.": 85,
    "В работе": 86,
    "Приостановлен": 87,
    "HR На рассмотрении": 88,
    "HR Кандидат приглашен на собеседование": 89,
    "HR Кандидат приглашен на тест-драйв": 90,
    "HR Прослушивание записи кандидата": 91,
    "HR Кандидат на рассмотрении службы безопасности": 92,
    "HR Кандидат одобрен": 93,
    "HR Кандидат отклонен": 94,
    "В процессе": 95,
    "Для бюджета": 96,
    "ООК - Ожидание ответа от клиента": 97,
    "ООК - В ожидании решения": 98,
    "Согласование с руководителем заявителя": 99,
    "В ожидании документов": 100,
    "Формирование бизнес-концепта": 101,
    "Разработка для бизнес-приложений": 102,
    "Тестирование функционала": 103,
    "Тестирование Заказчиком": 104,
    "Внедрение": 105,
    "ожидает ответ тк": 106,
    "ответ получен": 107,
    "Недозвон": 108,
    "подобрано РЦ": 109,
    "Отправлено заявителю": 110,
    "доставка заявителю": 111,
    "Согласование бизнес-концепта": 112,
    "Бизнес-концепт согласован": 113,
    "Согласование ": 114,
    "Исполение": 115,
    "В паузе": 116,
    "Уточнение задачи у заявителя": 117,
    "В работе у исполнителя": 118,
    "На Паузе/Отложен": 119,
    "Ознакомление с задачей": 120,
}

TASK_STATUSES_R = {x: y for y, x in TASK_STATUSES.items()}
TASK_STATUSES_DJANGO = [(x, TASK_STATUSES_R[x]) for x in TASK_STATUSES_R]

BRANDS = {
    "Lego": 0,
    "Restore": 1,
    "Samsung": 2,
    "Nike": 3,
    "Unode": 4,
    "Streetneat": 5,
    "Streetbeatkids": 6,
    "Streetbeatsport": 7,
    "Sony": 8,
    "Kidroks": 9,
    "Misia": 10
}
BRANDS_R = {x: y for y, x in TASK_STATUSES.items()}
BRANDS_DJANGO = [(x, BRANDS_R[x]) for x in BRANDS_R]

EXECUTOR_GROUP_IDS = {
    'Техподдержка': 1,
    '2-ая линия поддержки': 2,
    'Отдел ИТ': 3,
    'Отдел 1С': 4,
    'АРС': 5,
    'Курьер': 6,
    'Оператор КЦ': 7,
    'РСП': 8
}
EXECUTOR_GROUP_IDS_R = {x: y for y, x in EXECUTOR_GROUP_IDS.items()}

POSTPONED_TYPE = {
    'Неизвестно': 0,
    'Критическая завка': 1,
    'Отложена сотрудником': 2
}
POSTPONED_TYPE_R = {x: y for y, x in POSTPONED_TYPE.items()}
POSTPONED_TYPE_DJANGO = ((x, POSTPONED_TYPE_R[x]) for x in POSTPONED_TYPE_R)


class TelegramUser(models.Model):
    user_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=32, null=True)
    telephone = models.CharField(max_length=12, null=True, blank=True)

    def __str__(self):
        return f'TelegramUser({self.user_id})'


class TelegramTask(models.Model):
    current_step = models.CharField(max_length=128)

    brand = models.CharField(choices=BRANDS_DJANGO, max_length=32, null=True, blank=True)
    shop_fullname = models.CharField(max_length=128, null=True, blank=True)
    mobile_number = models.CharField(max_length=64, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    true_description = models.CharField(max_length=128, null=True, blank=True)
    kkm_number = models.CharField(max_length=128, null=True, blank=True)
    team_viewer = models.CharField(max_length=128, null=True, blank=True)
    screenshot = models.ImageField(upload_to="screenshots", null=True, blank=True)
    block_work = models.BooleanField(default=False)
    priority = models.IntegerField(choices=PRIORITY_STATUSES_DJANGO, null=True, blank=True)
    executor = models.ForeignKey('Executor', on_delete=models.SET_NULL, null=True, blank=True)
    is_mass = models.BooleanField(default=False)

    def name(self):
        description = str(self.true_description)[:50]
        return f"{self.brand}, {self.shop_fullname},  {description}, {self.mobile_number}"

    def intraservice_description(self):
        res = f'{self.true_description}\n'

        if self.kkm_number:
            res += f"Номер ККМ: {self.kkm_number}\n"

        client = Client.objects.get(telegram_task=self)

        if self.team_viewer:
            res += f'TeamViewer: {self.team_viewer}\n'
        else:
            res += 'TeamViewer: не указан\n'

        if client.telegram_user.username:
            res += f'Telegram: {client.telegram_user.username}\n'
        else:
            res += 'Telegram: не указан\n'

        if self.mobile_number:
            res += f'Телефон для связи: {self.mobile_number}\n'
        else:
            res += 'Телефон для связи: не указан\n'
        return res


class Client(models.Model):
    telegram_user = models.OneToOneField(TelegramUser, primary_key=True, on_delete=models.CASCADE)
    telegram_task = models.OneToOneField(TelegramTask, on_delete=models.SET_NULL, null=True, blank=True)


class IntraserviceUser(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=128)


class Executor(models.Model):
    intraservice_user = models.OneToOneField(IntraserviceUser, primary_key=True, on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=10, default='Не готов')
    last_status_change = models.DateTimeField(null=True, blank=True)
    telegram_user = models.OneToOneField(TelegramUser, unique=True, on_delete=models.DO_NOTHING)
    intraservice_task_active = models.OneToOneField('IntraserviceTask', on_delete=models.SET_NULL, null=True,
                                                    blank=True)

    def __str__(self):
        return f'Executor({self.intraservice_user.id})'


class Journal(models.Model):
    executor = models.ForeignKey(Executor, on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=32)
    from_time = models.DateTimeField()
    to_time = models.DateTimeField()


class BlockageJournal(models.Model):
    from_time = models.DateTimeField()
    to_time = models.DateTimeField()


class IntraserviceTask(models.Model):
    id = models.IntegerField(primary_key=True)
    priority = models.IntegerField(choices=PRIORITY_STATUSES_DJANGO, null=True, blank=True)
    telegram_client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.IntegerField(choices=TASK_STATUSES_DJANGO)
    postponed_type = models.IntegerField(choices=POSTPONED_TYPE_DJANGO, default=0)
    postponed_executor = models.ForeignKey('Executor', on_delete=models.SET_NULL, null=True, blank=True)
    executor_group = models.IntegerField(null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    edit_person = models.CharField(max_length=128, null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    is_mass = models.BooleanField(default=False)
    parent = models.ForeignKey('IntraserviceTask', on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now=True)
    long_execution_notification = models.DateTimeField(null=True, blank=True)
    executor_notification_count = models.IntegerField(default=0, null=True, blank=True)
    admin_notification = models.DateTimeField(null=True, blank=True)
    admin_notification_count = models.IntegerField(default=0, null=True, blank=True)

    @property
    def register_message(self):
        return (f"Заявка зарегистрирована и поставлена в очередь для работы в интрасервисе - номер заявки "
                f"*{self.id}*. Как только сотрудник возьмёт заявку в работу - я Вам сразу напишу.")

    @property
    def new_status_message(self):
        return (f"Для вашей заявки *{self.id}* сотрудником *{self.edit_person}* установлен "
                f"статус *{self.get_status_display()}*")

    @property
    def new_service_message(self):
        return (f"Ориентировочный срок устранения проблемы по вашей заявке *{self.description}* сотрудником "
                f"*{self.edit_person}*:\n*{self.deadline}*")

    def __lt__(self, other):
        priority = {
            'Низкий': 1,
            'Средний': 2,
            'Высокий': 3,
            'Критический': 4
        }

        if priority[PRIORITY_STATUSES_R[other.priority]] - priority[PRIORITY_STATUSES_R[self.priority]] == 0:
            if other.id > self.id:
                return True
            else:
                return False
        elif priority[PRIORITY_STATUSES_R[other.priority]] < priority[PRIORITY_STATUSES_R[self.priority]]:
            return True
        else:
            return False

    def __str__(self):
        return f'IntraserviceTask({self.id})'


class ExecutorStatistics(models.Model):
    executor = models.ForeignKey(Executor, on_delete=models.DO_NOTHING)
    date = models.DateField()
    ready_min = models.IntegerField(default=0)
    work_min = models.IntegerField(default=0)
    done_tasks = models.IntegerField(default=0)
    cancel_tasks = models.IntegerField(default=0)
    mass_tasks = models.IntegerField(default=0)
    postponed_tasks = models.IntegerField(default=0)
    postponed_notify = models.BooleanField(default=False)


class Statistic(models.Model):
    name = models.CharField(max_length=100)
    count = models.IntegerField(default=0)


class IntraserviceTest(models.Model):
    date = models.DateTimeField(auto_now=True)
    status = models.BooleanField()
    error = models.CharField(max_length=60)
