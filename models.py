import datetime

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
            # Для пропущенного - время окончания звонка, для входящего - время начала звонка
            'Дата и время',

            # Для входящего только тип
            'Тип', 'Номер звонка', 'Длительность дозвона',
            'Оператор',
            # Звонок, Обед
            'Действие',
            'Начало предобработки', 'Конец предобработки',
            'Начало звонка', 'Конец звонка',
            'Начало постобработки', 'Конец постобработки'
        ])
        self.operators = DataFrame(columns=[
            # Свободен, Постобработка, Предобработка входящего, Предобработка, Звонок, Обед
            'Номер', 'Статус', 'Время последнего освобождения', 'Время ближайшего освобождения'
        ])
        for i in range(OPERATOR_COUNT):
            row = [i + 1, 'Свободен', datetime.datetime.combine(DATE, datetime.time(9, 0, 0)), None]
            self.operators.loc[len(self.operators.index)] = row
