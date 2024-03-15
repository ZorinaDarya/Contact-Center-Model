import datetime
import warnings

import numpy as np
import pandas as pd
from pandas import DataFrame

from constants import DATE, DURATION_POSTPROCESSING_BACK_CALL, DURATION_PREPROCESSING_BACK_CALL, DURATION_BACK_CALL, \
    DURATION_PREPROCESSING_INCOMING_CALL, DURATION_INCOMING_CALL, DURATION_POSTPROCESSING_INCOMING_CALL, \
    DURATION_PREPROCESSING_OUTGOING_CALL, DURATION_OUTGOING_CALL, DURATION_POSTPROCESSING_OUTGOING_CALL, \
    OPERATOR_WAITING_BACK_CALL, OPERATOR_WAITING_OUTGOING_CALL
from google_sheets import update_tasks_cur
from markup_functions import change_task_type, wait_duration_class, get_action_class, get_sorted_tasks, check_group
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


def end_actions(moment):
    preprocessing_incoming_calls = model.actions[(model.actions['Тип задачи'] == 'Входящий') &
                                                 (model.actions['Завершена'] == 'Нет') &
                                                 (model.actions['Начало звонка'] > moment)]
    for index, row in preprocessing_incoming_calls.iterrows():
        task = model.tasks[model.tasks['ID'] == row['ID Задачи']].iloc[0]
        if task['Тип задачи'] == 'Пропущенный':
            model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                              (model.actions['Дата и время прерывания'] is None) &
                              (model.actions['Конец звонка'] == row['Конец звонка']), 'Завершена'] = 'Да'
            model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                              (model.actions['Дата и время прерывания'] is None) &
                              (model.actions['Конец звонка'] == row['Конец звонка']), 'Прервана'] = moment
            model.tasks.loc[model.tasks['ID'] == row['ID Задачи'], 'Обработана'] = 'Нет'
            model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Статус'] = 'Свободен'
            model.operators.loc[model.operators['Номер'] == row['Оператор'],
                                'Время последнего освобождения'] = moment
            model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Время ближайшего освобождения'] = None

    finished_actions = model.actions[(model.actions['Конец постобработки'] <= moment) &
                                     (model.actions['Завершена'] == 'Нет')]
    for index, row in finished_actions.iterrows():
        if row['Действие'] != 'Обед':
            model.tasks.loc[model.tasks['ID'] == row['ID Задачи'], 'Обработана'] = 'Да'

        model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Статус'] = 'Свободен'
        model.operators.loc[model.operators['Номер'] == row['Оператор'],
                            'Время последнего освобождения'] = row['Конец постобработки']
        model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Время ближайшего освобождения'] = None

        direction = row['Тип задачи'] if row['Тип задачи'] != 'Заявка' else 'Пропущенный'
        wait_duration = row['Длительность дозвона']
        callback_time = (row['Начало звонка'] - max(row['Дата и время'] + datetime.timedelta(seconds=row['Ожидание']),
                                                    datetime.datetime.combine(DATE,
                                                                              datetime.time(9, 0, 0)))).total_seconds()
        if direction == 'Пропущенный':
            model.classifier.loc[(model.classifier['Направление'] == direction) &
                                 (model.classifier['Тип'] == row['Тип']) &
                                 (model.classifier['Длительность дозвона'] == wait_duration) &
                                 (pd.isnull(model.classifier['Номер звонка'])) &
                                 (model.classifier['Начало'] <= callback_time) &
                                 (model.classifier['Конец'] > callback_time), 'Количество'] += 1
        elif direction == 'Входящий':
            model.classifier.loc[(model.classifier['Направление'] == direction) &
                                 (model.classifier['Тип'] == row['Тип']) &
                                 (pd.isnull(model.classifier['Номер звонка'])), 'Количество'] += 1
        else:
            model.classifier.loc[model.classifier['Направление'] == direction, 'Количество'] += 1

        model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                          (pd.isnull(model.actions['Дата и время прерывания'])) &
                          (model.actions['Начало звонка'] == row['Начало звонка']), 'Завершена'] = 'Да'


def update_tasks(moment):
    model.tasks['Тип задачи'] = model.tasks.apply(change_task_type, axis=1, moment=moment)
    model.tasks['Длительность дозвона'] = model.tasks.apply(wait_duration_class, axis=1)
    model.tasks['Приоритет'] = model.tasks.apply(get_action_class, axis=1, classifier=model.classifier,
                                                 moment=moment, param='Приоритет')
    model.tasks['Группа'] = model.tasks.apply(get_action_class, axis=1, classifier=model.classifier,
                                              moment=moment, param='Группа')


def get_new_task(moment):
    unprocessed_tasks = model.tasks[(model.tasks['Обработана'] == 'Нет') &
                                    (model.tasks['Тип задачи'] != 'Заявка') &
                                    (model.tasks['Тип'] != 'Прочее')]
    active_tasks = unprocessed_tasks[unprocessed_tasks['Приоритет'] == unprocessed_tasks['Приоритет'].min()]
    if not active_tasks.empty:
        new_task = get_sorted_tasks(active_tasks, moment)
        if not check_group(new_task, model, moment):
            new_task = None
    else:
        new_task = None
    return new_task


def assign_tasks(moment):
    free_operators = model.operators[model.operators['Статус'] == 'Свободен']
    for index, row in free_operators.iterrows():
        new_task = get_new_task(moment)
        if new_task is None:
            break
        else:
            if new_task['Тип задачи'] in ['Пропущенный', 'Заявка']:
                preprocessing = DURATION_PREPROCESSING_BACK_CALL + OPERATOR_WAITING_BACK_CALL
                call = DURATION_BACK_CALL
                postprocessing = DURATION_POSTPROCESSING_BACK_CALL
            elif new_task['Тип задачи'] == 'Входящий':
                preprocessing = DURATION_PREPROCESSING_INCOMING_CALL
                call = DURATION_INCOMING_CALL
                postprocessing = DURATION_POSTPROCESSING_INCOMING_CALL
            else:
                preprocessing = DURATION_PREPROCESSING_OUTGOING_CALL + OPERATOR_WAITING_OUTGOING_CALL
                call = DURATION_OUTGOING_CALL
                postprocessing = DURATION_POSTPROCESSING_OUTGOING_CALL

            action = DataFrame([[
                new_task['Тип задачи'],
                new_task['ID'],
                new_task['Дата и время'] if new_task['Тип задачи'] != 'Пропущенный'
                else new_task['Дата и время'] + datetime.timedelta(seconds=new_task['Ожидание']),
                new_task['Ожидание'],
                new_task['Тип'],
                new_task['Номер звонка'],
                new_task['Длительность дозвона'],
                index + 1,
                'Звонок',
                moment,
                moment + datetime.timedelta(seconds=preprocessing),
                moment + datetime.timedelta(seconds=preprocessing + call),
                moment + datetime.timedelta(seconds=preprocessing + call + postprocessing),

                None,
                'Нет'
            ]], columns=model.actions.columns)
            model.actions = pd.concat([model.actions, action])

            model.tasks.loc[model.tasks['ID'] == new_task['ID'], 'Обработана'] = 'В процессе'
            model.operators.loc[model.operators['Номер'] == index + 1, 'Статус'] = 'Задача'
            model.operators.loc[model.operators['Номер'] == index + 1, 'Время ближайшего освобождения'] = \
                moment + datetime.timedelta(seconds=preprocessing + call + postprocessing)


if __name__ == '__main__':
    a0 = datetime.datetime.now()
    start_point = datetime.datetime.combine(DATE, datetime.time(9, 0, 0))
    end_point = datetime.datetime.combine(DATE, datetime.time(21, 10, 0))
    cur_time = start_point

    model = init_model()
    # Добавление пропущенных в нерабочее время в список задач
    missed_calls_in_not_working_time(cur_time)
    a1 = datetime.datetime.now()
    while cur_time < end_point:
        a2 = datetime.datetime.now()

        # Определение какие события перешли в задачи
        check_incoming_application_flow(cur_time)

        # Изменение статусов задач: входящий/пропущенный, длительность дозвона, приоритет и группа, если появился второй
        # необработанный пропущенный с одного номера, то первый пропущенный "не активный"
        update_tasks(cur_time)

        # Завершение действий операторов, проставление времен, изменение статусов задач, изменение статусов операторов
        end_actions(cur_time)

        # По всем активным задачам пройтись: выбрать задачу, определить доступна ли группа, создать действие,
        # заполнить действие, изменить статус задачи, если есть еще
        # необработанный пропущенный с одного номера, то этот пропущенный уходит в архив

        assign_tasks(cur_time)
        # Если есть операторы в предобработке, то прерывать оператора, если есть входящий и
        # заново начинать новую задачу

        try:
            cur_time = min([model.incoming_application_flow[model.incoming_application_flow['Дата и время'] >
                                                            cur_time].iloc[0]['Дата и время'],

                            model.incoming_application_flow[(model.incoming_application_flow['Дата и время'] +
                                                             pd.to_timedelta(
                                                                 model.incoming_application_flow['Ожидание'], 's')) >
                                                            cur_time].iloc[0]['Дата и время'] +
                            pd.to_timedelta(
                                model.incoming_application_flow[(model.incoming_application_flow['Дата и время'] +
                                                                 pd.to_timedelta(
                                                                     model.incoming_application_flow['Ожидание'],
                                                                     's')) >
                                                                cur_time].iloc[0]['Ожидание'], 's'),
                            end_point if pd.isnull(
                                model.operators[model.operators['Статус'] != 'Свободен']
                                ['Время ближайшего освобождения'].min(skipna=True))
                            else model.operators[model.operators['Статус'] != 'Свободен']
                            ['Время ближайшего освобождения'].min(skipna=True),
                            datetime.datetime.combine(DATE, datetime.time(cur_time.hour + 1, 0, 0))])
        except:
            cur_time = end_point
        print(cur_time, datetime.datetime.now() - a2)

    # Сбор статистики

    a3 = datetime.datetime.now()
    update_tasks_cur(model.tasks, 'Лист8')
    update_tasks_cur(model.classifier, 'Лист9')
    update_tasks_cur(model.actions, 'Лист10')
    a4 = datetime.datetime.now()

    print('Загрузка входных данных: ', a1 - a0)
    print('Выполнение процесса: ', a3 - a1)
    print('Запись результатов: ', a4 - a3)
