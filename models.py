import datetime
import pandas as pd
from pandas import DataFrame
from constants import OPERATOR_COUNT, DATE, DURATION_PREPROCESSING_INCOMING_CALL, DEADLINE_BACK_CALL, \
    COUNT_OUTGOING_CALL, DURATION_LUNCH, COUNT_LUNCH, DURATION_BREAK, COUNT_BREAK


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
            'Приоритет', 'Группа'],
            data=[['Исходящий', str(i) + ' исходящая задача', datetime.datetime.now(), '7', int(0), int(0),
                   '', None, None, 'Исходящий', 'Нет', None, None] for i in range(COUNT_OUTGOING_CALL)])
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

        self.useful_points = self.useful_points.sort_values('Дата и время')
        self.statistic = DataFrame(columns=['Число'])

    def get_statistic(self, start, end):
        # 1 - 4
        count_input_applications = self.incoming_application_flow[
            (self.incoming_application_flow['Тип'].str.contains('Хочет записаться.')) &
            # (self.incoming_application_flow['Факт'] != 'Заявка') &
            (self.incoming_application_flow['Дата и время'] >= start) &
            (self.incoming_application_flow['Дата и время'] < end)].shape[0]
        count_short_input_applications = self.incoming_application_flow[
            (self.incoming_application_flow['Тип'].str.contains('Хочет записаться.')) &
            # (self.incoming_application_flow['Факт'] != 'Заявка') &
            (self.incoming_application_flow['Ожидание'] < 5) &
            (self.incoming_application_flow['Дата и время'] >= start) &
            (self.incoming_application_flow['Дата и время'] < end)].shape[0]
        count_insufficient_input_applications = self.incoming_application_flow[
            (self.incoming_application_flow['Тип'].str.contains('Хочет записаться.')) &
            # (self.incoming_application_flow['Факт'] != 'Заявка') &
            (self.incoming_application_flow['Ожидание'] >= 5) &
            (self.incoming_application_flow['Ожидание'] < DURATION_PREPROCESSING_INCOMING_CALL) &
            (self.incoming_application_flow['Дата и время'] >= start) &
            (self.incoming_application_flow['Дата и время'] < end)].shape[0]
        count_sufficient_input_applications = self.incoming_application_flow[
            (self.incoming_application_flow['Тип'].str.contains('Хочет записаться.')) &
            # (self.incoming_application_flow['Факт'] != 'Заявка') &
            (self.incoming_application_flow['Ожидание'] >= DURATION_PREPROCESSING_INCOMING_CALL) &
            (self.incoming_application_flow['Дата и время'] >= start) &
            (self.incoming_application_flow['Дата и время'] < end)].shape[0]
        count_requests = self.incoming_application_flow[
            (self.incoming_application_flow['Тип'].str.contains('Хочет записаться.')) &
            (self.incoming_application_flow['Факт'] == 'Заявка') &
            (self.incoming_application_flow['Ожидание'] >= DURATION_PREPROCESSING_INCOMING_CALL) &
            (self.incoming_application_flow['Дата и время'] >= start) &
            (self.incoming_application_flow['Дата и время'] < end)].shape[0]
        self.statistic.loc[len(self.statistic.index)] = [count_input_applications]
        self.statistic.loc[len(self.statistic.index)] = [count_short_input_applications]
        self.statistic.loc[len(self.statistic.index)] = [count_insufficient_input_applications]
        self.statistic.loc[len(self.statistic.index)] = [count_sufficient_input_applications]
        self.statistic.loc[len(self.statistic.index)] = [count_requests]

        print(count_input_applications, count_short_input_applications, count_insufficient_input_applications,
              count_sufficient_input_applications, count_requests)

        # 5 - 7
        count_incoming_call = self.actions[
            (self.actions['Тип задачи'] == 'Входящий') &
            (pd.isnull(self.actions['Дата и время прерывания']))].shape[0]
        per_count_incoming_call_all = count_incoming_call / count_input_applications
        per_count_incoming_call_sufficient = count_incoming_call / count_sufficient_input_applications
        per_count_call_without_requests = count_incoming_call / (count_sufficient_input_applications - count_requests)
        self.statistic.loc[len(self.statistic.index)] = [count_incoming_call]
        self.statistic.loc[len(self.statistic.index)] = [per_count_incoming_call_all]
        self.statistic.loc[len(self.statistic.index)] = [per_count_incoming_call_sufficient]
        self.statistic.loc[len(self.statistic.index)] = [per_count_call_without_requests]
        print(count_incoming_call, per_count_incoming_call_all, per_count_incoming_call_sufficient,
              per_count_call_without_requests)

        # 8 - 11
        count_missed_call = self.tasks[(self.tasks['Тип задачи'] != 'Входящий') &
                                       (self.tasks['Тип задачи'] != 'Исходящий') &
                                       (self.tasks['Тип'].str.contains('Хочет записаться.')) &
                                       (self.tasks['Дата и время'] >= start) &
                                       (self.tasks['Дата и время'] < end)].shape[0]
        count_normal_missed_call = None
        per_count_back_call_all = count_missed_call / count_input_applications
        per_count_back_call_sufficient = self.tasks[
                                             (self.tasks['Тип'].str.contains('Хочет записаться.')) &
                                             (self.tasks['Ожидание'] >= DURATION_PREPROCESSING_INCOMING_CALL) &
                                             (self.tasks['Тип задачи'] == 'Пропущенный') &
                                             (self.tasks['Дата и время'] >= start) &
                                             (self.tasks['Дата и время'] < end)].shape[
                                             0] / count_sufficient_input_applications
        self.statistic.loc[len(self.statistic.index)] = [count_missed_call]
        self.statistic.loc[len(self.statistic.index)] = [count_normal_missed_call]
        self.statistic.loc[len(self.statistic.index)] = [per_count_back_call_all]
        self.statistic.loc[len(self.statistic.index)] = [per_count_back_call_sufficient]
        print(count_missed_call, count_normal_missed_call, per_count_back_call_all, per_count_back_call_sufficient)

        # 12 - 16
        count_back_call = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end)].shape[
            0]
        count_non_back_call = self.tasks[
            (self.tasks['Тип'].str.contains('Хочет записаться.')) &
            (self.tasks['Тип задачи'] != 'Исходящий') &
            (self.tasks['Тип задачи'] != 'Входящий') &
            (self.tasks['Обработана'] == 'Нет') &
            (self.tasks['Дата и время'] >= start) &
            (self.tasks['Дата и время'] < end)].shape[
            0]
        count_non_processed_call = None
        per_count_non_back_call = count_non_back_call / count_input_applications
        per_count_non_processed_call = None
        self.statistic.loc[len(self.statistic.index)] = [count_back_call]
        self.statistic.loc[len(self.statistic.index)] = [count_non_back_call]
        self.statistic.loc[len(self.statistic.index)] = [count_non_processed_call]
        self.statistic.loc[len(self.statistic.index)] = [per_count_non_back_call]
        self.statistic.loc[len(self.statistic.index)] = [per_count_non_processed_call]
        print(count_back_call, count_non_back_call, count_non_processed_call, per_count_non_back_call,
              per_count_non_processed_call)

        # 17 - 20
        count_back_call_in_deadline = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions[
                'Дата и время']).dt.total_seconds() <= DEADLINE_BACK_CALL)].shape[0]
        count_connection_in_deadline = count_incoming_call + count_back_call_in_deadline
        per_count_connection_in_deadline = count_connection_in_deadline / count_input_applications
        per_count_back_call_in_deadline = count_back_call_in_deadline / count_back_call
        self.statistic.loc[len(self.statistic.index)] = [count_connection_in_deadline]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_in_deadline]
        self.statistic.loc[len(self.statistic.index)] = [per_count_connection_in_deadline]
        self.statistic.loc[len(self.statistic.index)] = [per_count_back_call_in_deadline]
        print(count_connection_in_deadline, count_back_call_in_deadline, per_count_connection_in_deadline,
              per_count_back_call_in_deadline)

        # 21 - 29
        count_back_call_sec_1 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 1 * 60)].shape[0]
        count_back_call_sec_2 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 2 * 60) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 1 * 60)].shape[0]
        count_back_call_sec_3 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 3 * 60) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 2 * 60)].shape[0]
        count_back_call_sec_4 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 4 * 60) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 3 * 60)].shape[0]
        count_back_call_sec_5 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 5 * 60) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 4 * 60)].shape[0]
        count_back_call_sec_10 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 10 * 60) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 5 * 60)].shape[0]
        count_back_call_sec_20 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 20 * 60) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 10 * 60)].shape[0]
        count_back_call_sec_30 = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() <= 30 * 60) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 20 * 60)].shape[0]
        count_back_call_sec_last = self.actions[
            (self.actions['Тип'].str.contains('Хочет записаться.')) &
            (self.actions['Тип задачи'] != 'Исходящий') &
            (self.actions['Тип задачи'] != 'Входящий') &
            (self.actions['Дата и время'] >= start) &
            (self.actions['Дата и время'] < end) &
            ((self.actions['Начало звонка'] - self.actions['Дата и время']).dt.total_seconds() > 30 * 60)].shape[0]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_1]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_2]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_3]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_4]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_5]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_10]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_20]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_30]
        self.statistic.loc[len(self.statistic.index)] = [count_back_call_sec_last]
        print(count_back_call_sec_1, count_back_call_sec_2, count_back_call_sec_3, count_back_call_sec_4,
              count_back_call_sec_5, count_back_call_sec_10, count_back_call_sec_20, count_back_call_sec_30,
              count_back_call_sec_last)

        # 30 - 31
        count_outgoing_call = self.actions[
            (self.actions['Тип задачи'] == 'Исходящий') &
            (pd.isnull(self.actions['Дата и время прерывания']))].shape[0]
        per_count_outgoing_call = count_outgoing_call / COUNT_OUTGOING_CALL
        self.statistic.loc[len(self.statistic.index)] = [count_outgoing_call]
        self.statistic.loc[len(self.statistic.index)] = [per_count_outgoing_call]
        print(count_outgoing_call, per_count_outgoing_call)

        # 32 - 36
        sec_schedule = OPERATOR_COUNT * ((end - start).total_seconds() -
                                         DURATION_LUNCH * COUNT_LUNCH - DURATION_BREAK * COUNT_BREAK)
        actions = self.actions[(self.actions['Тип'].str.contains('Хочет записаться.')) | (self.actions['Тип'] == '')]
        df_sec_in_call = (actions['Начало постобработки'] - actions['Начало звонка']).dt.total_seconds()
        sec_in_call = df_sec_in_call.sum()
        df_sec_costs_pred = (actions['Начало звонка'] - actions['Начало предобработки']).dt.total_seconds()
        df_sec_costs_post = (actions['Конец постобработки'] - actions['Начало постобработки']).dt.total_seconds()
        sec_costs = df_sec_costs_pred.sum() + df_sec_costs_post.sum()
        workload = sec_in_call / sec_schedule
        workload_with_costs = (sec_costs + sec_in_call) / sec_schedule
        self.statistic.loc[len(self.statistic.index)] = [sec_schedule]
        self.statistic.loc[len(self.statistic.index)] = [sec_in_call]
        self.statistic.loc[len(self.statistic.index)] = [sec_costs]
        self.statistic.loc[len(self.statistic.index)] = [workload]
        self.statistic.loc[len(self.statistic.index)] = [workload_with_costs]
        print(sec_schedule, sec_in_call, sec_costs, workload, workload_with_costs)

        # 37 - 48
        # расчёт в таблице
