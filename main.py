import datetime
import warnings
import pandas as pd
from pandas import DataFrame

from constants import DATE
from google_sheets import update_tasks_cur
from markup_functions import change_task_type, wait_duration_class, get_action_class
from model_initialization import init_model

warnings.filterwarnings('ignore')


def missed_calls_in_not_working_time(moment):
    missed_events = model.incoming_application_flow[model.incoming_application_flow['Дата и время'] < moment]
    for index, row in missed_events.iterrows():
        task = DataFrame([[row['Факт'],
                           row['ID'],
                           row['Дата и время'],
                           row['Телефон'],
                           row['Ожидание'],
                           row['Разговор'],
                           row['Тип'],
                           row['Номер звонка'],
                           None,
                           'Пропущенный' if row['Факт'] != 'Заявка' else row['Факт'],
                           'Нет',
                           None,
                           None]], columns=model.tasks.columns)
        # model.tasks.loc[len(model.tasks.index)] = task
        model.tasks = pd.concat([model.tasks, task])


def check_incoming_application_flow(moment):
    upcoming_events = model.incoming_application_flow[model.incoming_application_flow['Дата и время'] == moment]
    for index, row in upcoming_events.iterrows():
        task = DataFrame([[row['Факт'],
                           row['ID'],
                           row['Дата и время'],
                           row['Телефон'],
                           row['Ожидание'],
                           row['Разговор'],
                           row['Тип'],
                           row['Номер звонка'],
                           None,
                           'Входящий' if row['Факт'] != 'Заявка' else row['Факт'],
                           'Нет',
                           None,
                           None]], columns=model.tasks.columns)
        model.tasks = pd.concat([model.tasks, task])
        # model.tasks.loc[len(model.tasks.index)] = task


def update_tasks(moment):
    model.tasks['Тип задачи'] = model.tasks.apply(change_task_type, axis=1, moment=moment)
    model.tasks['Длительность дозвона'] = model.tasks.apply(wait_duration_class, axis=1)
    model.tasks['Приоритет'] = model.tasks.apply(get_action_class, axis=1, classifier=model.classifier,
                                                 moment=moment, param='Приоритет')
    model.tasks['Группа'] = model.tasks.apply(get_action_class, axis=1, classifier=model.classifier,
                                              moment=moment, param='Группа')


if __name__ == '__main__':
    a0 = datetime.datetime.now()
    start_point = datetime.datetime.combine(DATE, datetime.time(9, 0, 0))
    end_point = datetime.datetime.combine(DATE, datetime.time(10, 0, 0))
    cur_time = start_point

    model = init_model()
    # Добавление пропущенных в нерабочее время в список задач
    missed_calls_in_not_working_time(cur_time)
    a1 = datetime.datetime.now()
    while cur_time <= end_point:
        a2 = datetime.datetime.now()

        # Определение какие события перешли в задачи
        check_incoming_application_flow(cur_time)
        # Изменение статусов задач: входящий/пропущенный, длительность дозвона, приоритет и группа, если появился второй
        # необработанный пропущенный с одного номера, то первый пропущенный "не активный"
        update_tasks(cur_time)
        # Завершение действий операторов, проставление времен, изменение статусов задач, изменение статусов операторов

        # По всем активным задачам пройтись: выбрать задачу, определить доступна ли группа, создать действие,
        # заполнить действие, изменить статус задачи

        # Сбор статистики

        cur_time += datetime.timedelta(seconds=1)
        print(cur_time, datetime.datetime.now() - a2)

    a3 = datetime.datetime.now()
    update_tasks_cur(model.tasks)
    a4 = datetime.datetime.now()

    print('Загрузка входных данных: ', a1 - a0)
    print('Выполнение процесса: ', a3 - a1)
    print('Запись результатов: ', a4 - a3)
