import datetime
import pandas as pd
from pandas import DataFrame
from constants import OPERATOR_COUNT, DATE


class Model:
    def __init__(self, input_data, classifier, available_groups, schedule):
        self.incoming_application_flow = input_data
        self.classifier = classifier
        self.available_groups = available_groups
        self.schedule = schedule
        self.tasks = DataFrame(columns=[
            'Факт', 'ID', 'Дата и время', 'Телефон', 'Ожидание', 'Разговор',

            'Тип',
            # Сейчас заглушка
            'Номер звонка',
            # Только у пропущенных
            'Длительность дозвона',

            # Входящий, Пропущенный, Заявка, Исходящий
            'Тип задачи',
            # Да, Нет, В процессе, Архив
            'Обработана',
            # Определяются по матрице
            'Приоритет', 'Группа'
        ])
        self.actions = DataFrame(columns=[
            'Тип задачи',
            'ID Задачи',
            'Дата и время',
            'Ожидание',

            # Для входящего только тип
            'Тип', 'Номер звонка', 'Длительность дозвона',
            'Оператор',
            # Звонок, Обед
            'Действие',

            'Начало предобработки',
            'Начало звонка',
            'Начало постобработки',
            'Конец постобработки',

            'Дата и время прерывания',
            'Завершена'
        ])
        self.operators = DataFrame(columns=[
            # Свободен, Задача, Перерыв
            'Номер', 'Статус', 'Время последнего освобождения', 'Время ближайшего освобождения'
        ])
        for i in range(OPERATOR_COUNT):
            row = [i + 1, 'Свободен', datetime.datetime.combine(DATE, datetime.time(9, 0, 0)), None]
            self.operators.loc[len(self.operators.index)] = row

        self.useful_points = DataFrame(columns=['Дата и время'])
        self.useful_points['Дата и время'] = self.incoming_application_flow['Дата и время'] + \
                                             pd.to_timedelta(self.incoming_application_flow['Ожидание'], 's')

        self.useful_points = pd.concat([
            self.useful_points,
            self.incoming_application_flow['Дата и время']
        ])

        break_beginnings = self.schedule.rename(columns={str(OPERATOR_COUNT) + ' начало': 'Дата и время'})
        break_beginnings = break_beginnings[pd.notnull(break_beginnings['Дата и время'])]['Дата и время']

        self.useful_points = pd.concat([
            self.useful_points,
            break_beginnings
        ])

        break_endings = self.schedule.rename(columns={str(OPERATOR_COUNT) + ' конец': 'Дата и время'})
        break_endings = break_endings[pd.notnull(break_endings['Дата и время'])]['Дата и время']

        self.useful_points = pd.concat([
            self.useful_points,
            break_endings
        ])

        # self.useful_points = pd.concat([
        #     self.useful_points,
        #     (self.incoming_application_flow['Дата и время'] +
        #      pd.to_timedelta(self.incoming_application_flow['Ожидание'], 's'))
        # ])
        self.useful_points = self.useful_points.sort_values('Дата и время')



