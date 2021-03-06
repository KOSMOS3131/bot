# Generated by Django 2.1.4 on 2019-01-12 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0019_auto_20190110_1850'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telegramtask',
            name='brand',
            field=models.CharField(blank=True, choices=[(31, 'Открыта'), (27, 'В работе'), (35, 'Требует уточнения'), (26, 'Отложена'), (29, 'Выполнена'), (28, 'Закрыта'), (30, 'Отменена'), (43, 'Передано в ИТ отдел'), (44, 'Передано в ТП'), (39, 'Передано АРС'), (40, 'Передано курьеру'), (42, 'Выполнено(АРС)'), (41, 'В работе(АРС)'), (45, 'Открыта(АРС)'), (47, 'Передано начальнику службы обеспечения'), (48, 'Передано начальнику отдела внутренней безопасности'), (49, 'Начальник АХО'), (51, 'Проверено КЦ'), (52, 'Передано в отдел Разработки'), (53, 'Передано РСП'), (54, 'Некомпетентность'), (55, 'Отложенный старт')], max_length=16, null=True),
        ),
    ]
