import datetime

import numpy as np
import pandas as pd

from constants import PATIENT_WAITING, DURATION_INCOMING_CALL, DATE


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
    if row['Тип задачи'] == 'Пропущенный' and row['Длительность дозвона'] is None:
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
