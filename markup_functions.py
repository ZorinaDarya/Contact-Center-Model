import datetime

import numpy as np
import pandas as pd

from constants import PATIENT_WAITING, DURATION_INCOMING_CALL, DATE, AVAILABLE_ACTIONS_SELECTION_MODE, OPERATOR_COUNT


def wait_calculation(row):
    if row['Факт'] != 'Взят':
        val = row['Ожидание']
    else:
        val = max(PATIENT_WAITING, row['Ожидание'])

    return val


def talk_calculation(row):
    if row['Факт'] == 'Взят':
        val = row['Разговор']
    else:
        val = DURATION_INCOMING_CALL

    return val


def change_task_type(row, moment):
    if row['Тип задачи'] == 'Входящий' \
            and row['Обработана'] == 'Нет' \
            and row['Дата и время'] + datetime.timedelta(seconds=row['Ожидание']) <= moment:
        val = 'Пропущенный'
    else:
        val = row['Тип задачи']

    return val


def wait_duration_class(row):
    if row['Тип задачи'] == 'Пропущенный' and pd.isnull(row['Длительность дозвона']):
        if row['Ожидание'] < 5:
            val = '0 - 5'
        elif row['Ожидание'] >= 20:
            val = '20+'
        else:
            val = '5 - 20'
    else:
        val = row['Длительность дозвона']

    return val


def get_action_class(row, classifier, moment, param):
    if row['Обработана'] == 'Нет':
        direction = row['Тип задачи'] if row['Тип задачи'] != 'Заявка' else 'Пропущенный'
        wait_duration = row['Длительность дозвона'] if row['Тип задачи'] != 'Заявка' else '20+'
        callback_time = (moment - max(row['Дата и время'] + datetime.timedelta(seconds=row['Ожидание']),
                                      datetime.datetime.combine(DATE, datetime.time(9, 0, 0)))).total_seconds()
        if direction == 'Пропущенный':
            task_class = classifier[(classifier['Направление'] == direction) &
                                    (classifier['Тип'] == row['Тип']) &
                                    (classifier['Длительность дозвона'] == wait_duration) &
                                    (pd.isnull(classifier['Номер звонка'])) &
                                    (classifier['Начало'] <= callback_time) &
                                    (classifier['Конец'] > callback_time)]
        elif direction == 'Входящий':
            task_class = classifier[(classifier['Направление'] == direction) &
                                    (classifier['Тип'] == row['Тип']) &
                                    (pd.isnull(classifier['Номер звонка']))]
        else:
            task_class = classifier[classifier['Направление'] == direction]
        try:
            val = task_class.iloc[0][param]
        except IndexError:
            val = None
    else:
        val = row[param]

    return val


def get_sorted_tasks(df, moment):
    df = df.sort_values('Дата и время')
    callback_time = (moment - max(df.iloc[0]['Дата и время'] + datetime.timedelta(seconds=df.iloc[0]['Ожидание']),
                                  datetime.datetime.combine(DATE, datetime.time(9, 0, 0)))).total_seconds()
    if df.iloc[0]['Тип задачи'] == 'Пропущенный' and callback_time >= 5 * 60:
        val = df.iloc[-1]
    else:
        val = df.iloc[0]
    return val


def call_number_classification(row):
    return None


def type_classification(row, ident):
    try:
        ident_type = ident[((ident['Телефон'] == row['Телефон']) &
                            (ident['Дата и время'] <= row['Дата и время']) &
                            (ident['Ожидание'] == row['Ожидание']) &
                            (ident['Длительность'] == row['Разговор']))].iloc[0]['Тип']
    except IndexError as e:
        # print('-----------------------------------------')
        # print('Warning "Не нашлось такого звонка в IDENT"\n', row, str(e))
        ident_type = 'Хочет записаться.'
    return ident_type


def check_group(row, model, moment):
    available_group_number = 0
    if AVAILABLE_ACTIONS_SELECTION_MODE == 'TIME':
        available_group_numbers = model.available_groups[(model.available_groups['Начало'] <= moment.hour) &
                                                         (model.available_groups['Конец'] > moment.hour)]
        available_group_number = available_group_numbers.iloc[0, moment.weekday()]
    elif AVAILABLE_ACTIONS_SELECTION_MODE == 'FREE_OPERATOR':
        free_operators = model.operators[model.operators['Статус'] == 'Свободен']
        if free_operators.empty:
            available_group_number = 0
        else:
            available_group_number = free_operators.shape[0]
    if row['Группа'] > available_group_number:
        val = False
    else:
        val = True
    return val


def get_operator_break(num, moment, schedule):
    breaks = schedule[(schedule['Перерыв'].str.contains('Сотрудник ' + str(num + 1))) &
                      (schedule[str(OPERATOR_COUNT) + ' конец'] > moment) &
                      (schedule[str(OPERATOR_COUNT) + ' начало'] <= moment) &
                      (pd.notnull(schedule[str(OPERATOR_COUNT) + ' начало']))]
    if breaks.empty:
        val = False
        end_time = None
    else:
        val = True
        end_time = breaks.iloc[0][str(num + 1) + ' конец']

    return val, end_time

