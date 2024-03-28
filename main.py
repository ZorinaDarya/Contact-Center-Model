import datetime
import warnings
import pandas as pd
from pandas import DataFrame

from constants import DATE, DURATION_POSTPROCESSING_BACK_CALL, DURATION_PREPROCESSING_BACK_CALL, DURATION_BACK_CALL, \
    DURATION_PREPROCESSING_INCOMING_CALL, DURATION_POSTPROCESSING_INCOMING_CALL, \
    DURATION_PREPROCESSING_OUTGOING_CALL, DURATION_OUTGOING_CALL, DURATION_POSTPROCESSING_OUTGOING_CALL, \
    OPERATOR_WAITING_BACK_CALL, OPERATOR_WAITING_OUTGOING_CALL, OPERATOR_COUNT, GROUP_MATRIX
from google_sheets import update_tasks_cur, save_day
from markup_functions import change_task_type, wait_duration_class, get_action_class, get_sorted_tasks, check_group, \
    get_operator_break, send_to_archive
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
                           'Входящий' if row['Факт'] != 'Заявка' else 'Заявка',
                           'Нет',
                           None,
                           None]], columns=model.tasks.columns)
        model.tasks = pd.concat([model.tasks, task])
        # model.tasks.loc[len(model.tasks.index)] = task


def update_tasks(moment, d):
    model.tasks['Обработана'] = model.tasks.apply(send_to_archive, axis=1, moment=moment)
    model.tasks['Тип задачи'] = model.tasks.apply(change_task_type, axis=1, moment=moment)
    model.tasks['Длительность дозвона'] = model.tasks.apply(wait_duration_class, axis=1)
    model.tasks['Приоритет'] = model.tasks.apply(get_action_class, axis=1, classifier=model.classifier,
                                                 moment=moment, param='Приоритет', d=d)
    model.tasks['Группа'] = model.tasks.apply(get_action_class, axis=1, classifier=model.classifier,
                                              moment=moment, param='Группа', d=d)


def get_new_task(moment):
    unprocessed_tasks = model.tasks[(model.tasks['Обработана'] == 'Нет')]
    # & (model.tasks['Тип'] != 'Прочее')]
    active_tasks = unprocessed_tasks[unprocessed_tasks['Приоритет'] == unprocessed_tasks['Приоритет'].min()]
    if not active_tasks.empty:
        new_task = get_sorted_tasks(active_tasks, moment, d)
        if not check_group(new_task, model, moment):
            new_task = None
    else:
        new_task = None
    return new_task


def end_actions(moment, d, oc):
    break_operators = model.operators[model.operators['Статус'] == 'Перерыв']
    for index, row in break_operators.iterrows():
        operator_break, end_time = get_operator_break(index, moment, model.schedule, oc)
        if not operator_break:
            model.operators.loc[model.operators['Номер'] == index + 1, 'Статус'] = 'Свободен'
            model.operators.loc[model.operators['Номер'] == index + 1, 'Время последнего освобождения'] = moment
            model.operators.loc[model.operators['Номер'] == index + 1, 'Время ближайшего освобождения'] = end_time

    preprocessing_incoming_calls_others = model.actions[(model.actions['Тип задачи'] == 'Входящий') &
                                                        (model.actions['Завершена'] == 'Нет') &
                                                        (model.actions['Тип'] == 'Прочее') &
                                                        ((model.actions['Начало звонка'] <= moment) |
                                                         (model.actions['Дата и время'] +
                                                          pd.to_timedelta(model.actions['Ожидание'], 's') <= moment))]
    for index, row in preprocessing_incoming_calls_others.iterrows():
        model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                          (pd.isnull(model.actions['Дата и время прерывания'])) &
                          (model.actions['Конец постобработки'] == row['Конец постобработки']), 'Завершена'] = 'Да'
        model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                          (pd.isnull(model.actions['Дата и время прерывания'])) &
                          (model.actions['Конец постобработки'] == row['Конец постобработки']),
                          'Дата и время прерывания'] = moment
        model.tasks.loc[model.tasks['ID'] == row['ID Задачи'], 'Обработана'] = 'Сброшена'
        model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Статус'] = 'Свободен'
        model.operators.loc[model.operators['Номер'] == row['Оператор'],
                            'Время последнего освобождения'] = moment
        model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Время ближайшего освобождения'] = None

    preprocessing_incoming_calls = model.actions[(model.actions['Тип задачи'] == 'Входящий') &
                                                 (model.actions['Завершена'] == 'Нет') &
                                                 (model.actions['Начало звонка'] > moment) &
                                                 (model.actions['Тип'] != 'Прочее')]
    for index, row in preprocessing_incoming_calls.iterrows():
        task = model.tasks[model.tasks['ID'] == row['ID Задачи']].iloc[0]
        if task['Дата и время'] + datetime.timedelta(seconds=int(task['Ожидание'])) < row['Начало звонка']:
            model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                              (pd.isnull(model.actions['Дата и время прерывания'])) &
                              (model.actions['Конец постобработки'] == row['Конец постобработки']), 'Завершена'] = 'Да'
            model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                              (pd.isnull(model.actions['Дата и время прерывания'])) &
                              (model.actions['Конец постобработки'] == row['Конец постобработки']),
                              'Дата и время прерывания'] = moment
            model.tasks.loc[model.tasks['ID'] == row['ID Задачи'], 'Обработана'] = 'Нет'
            model.tasks.loc[model.tasks['ID'] == row['ID Задачи'], 'Тип задачи'] = 'Пропущенный'
            model.tasks.loc[model.tasks['ID'] == row['ID Задачи'], 'Длительность дозвона'] = \
                wait_duration_class(model.tasks[model.tasks['ID'] == row['ID Задачи']].iloc[0])
            model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Статус'] = 'Свободен'
            model.operators.loc[model.operators['Номер'] == row['Оператор'],
                                'Время последнего освобождения'] = moment
            model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Время ближайшего освобождения'] = None

    finished_actions = model.actions[(model.actions['Конец постобработки'] <= moment) &
                                     (model.actions['Завершена'] == 'Нет')]
    for index, row in finished_actions.iterrows():
        model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Статус'] = 'Свободен'
        model.operators.loc[model.operators['Номер'] == row['Оператор'],
                            'Время последнего освобождения'] = row['Конец постобработки']
        model.operators.loc[model.operators['Номер'] == row['Оператор'], 'Время ближайшего освобождения'] = None

        if row['Действие'] != 'Обед':
            # if row['Тип задачи'] != 'Исходящий':
            model.tasks.loc[model.tasks['ID'] == row['ID Задачи'], 'Обработана'] = 'Да'

            if row['Тип задачи'] == 'Пропущенный':
                callback_time = (row['Начало звонка'] -
                                 max(row['Дата и время'] + datetime.timedelta(seconds=int(row['Ожидание'])),
                                     datetime.datetime.combine(DATE[d], datetime.time(9, 0, 0)))).total_seconds()
                if row['Дата и время'] >= datetime.datetime.combine(DATE[d], datetime.time(9, 0, 0)):
                    model.classifier.loc[(model.classifier['Направление'] == row['Тип задачи']) &
                                         (model.classifier['Тип'] == row['Тип']) &
                                         (model.classifier['Длительность дозвона'] == row['Длительность дозвона']) &
                                         (pd.isnull(model.classifier['Номер звонка'])) &
                                         (model.classifier['Начало'] <= callback_time) &
                                         (model.classifier['Конец'] > callback_time), 'Количество звонков'] += 1
            elif row['Тип задачи'] == 'Заявка':
                callback_time = (row['Начало звонка'] - max(row['Дата и время'],
                                 datetime.datetime.combine(DATE[d], datetime.time(9, 0, 0)))).total_seconds()
                if row['Дата и время'] >= datetime.datetime.combine(DATE[d], datetime.time(9, 0, 0)):
                    model.classifier.loc[(model.classifier['Направление'] == 'Пропущенный') &
                                         (model.classifier['Тип'] == row['Тип']) &
                                         (model.classifier['Длительность дозвона'] == row['Длительность дозвона']) &
                                         (pd.isnull(model.classifier['Номер звонка'])) &
                                         (model.classifier['Начало'] <= callback_time) &
                                         (model.classifier['Конец'] > callback_time), 'Количество заявок'] += 1
            elif row['Тип задачи'] == 'Входящий':
                model.classifier.loc[(model.classifier['Направление'] == row['Тип задачи']) &
                                     (model.classifier['Тип'] == row['Тип']) &
                                     (pd.isnull(model.classifier['Номер звонка'])), 'Количество звонков'] += 1
            else:
                model.classifier.loc[model.classifier['Направление'] == row['Тип задачи'], 'Количество звонков'] += 1

            model.actions.loc[(model.actions['ID Задачи'] == row['ID Задачи']) &
                              (pd.isnull(model.actions['Дата и время прерывания'])) &
                              (model.actions['Начало звонка'] == row['Начало звонка']), 'Завершена'] = 'Да'


def assign_tasks(moment, oc):
    free_operators = model.operators[model.operators['Статус'] == 'Свободен']
    for index, row in free_operators.iterrows():
        operator_break, end_time = get_operator_break(index, moment, model.schedule, oc)
        if operator_break:
            model.operators.loc[model.operators['Номер'] == index + 1, 'Статус'] = 'Перерыв'
            model.operators.loc[model.operators['Номер'] == index + 1, 'Время ближайшего освобождения'] = end_time
        else:
            new_task = get_new_task(moment)
            if new_task is None:
                break
            else:
                if new_task['Тип задачи'] in ['Пропущенный', 'Заявка']:
                    preprocessing = DURATION_PREPROCESSING_BACK_CALL
                    call = int((DURATION_BACK_CALL if new_task['Факт'] == 'Пропущен' else new_task['Разговор']) +
                               OPERATOR_WAITING_BACK_CALL)
                    postprocessing = DURATION_POSTPROCESSING_BACK_CALL
                elif new_task['Тип задачи'] == 'Входящий':
                    preprocessing = DURATION_PREPROCESSING_INCOMING_CALL
                    call = int(new_task['Разговор'])
                    postprocessing = DURATION_POSTPROCESSING_INCOMING_CALL
                else:
                    preprocessing = DURATION_PREPROCESSING_OUTGOING_CALL
                    call = DURATION_OUTGOING_CALL + OPERATOR_WAITING_OUTGOING_CALL
                    postprocessing = DURATION_POSTPROCESSING_OUTGOING_CALL

                action = DataFrame([[
                    new_task['Тип задачи'],
                    new_task['ID'],
                    new_task['Дата и время'],
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

                # if new_task['Тип задачи'] != 'Исходящий':
                model.tasks.loc[model.tasks['ID'] == new_task['ID'], 'Обработана'] = 'В процессе'
                model.operators.loc[model.operators['Номер'] == index + 1, 'Статус'] = 'Задача'
                model.operators.loc[model.operators['Номер'] == index + 1, 'Время ближайшего освобождения'] = \
                    moment + datetime.timedelta(seconds=preprocessing + call + postprocessing)


if __name__ == '__main__':
    for d in range(len(DATE)):
        for m in range(len(GROUP_MATRIX)):
            for oc in range(len(OPERATOR_COUNT)):

                a0 = datetime.datetime.now()
                start_point = datetime.datetime.combine(DATE[d], datetime.time(9, 0, 0))
                end_point = datetime.datetime.combine(DATE[d], datetime.time(21, 0, 0))
                cur_time = start_point
                model = init_model(d, m, oc)

                # Добавление пропущенных в нерабочее время в список задач
                missed_calls_in_not_working_time(cur_time)
                a1 = datetime.datetime.now()
                while cur_time < end_point:
                    a2 = datetime.datetime.now()
                    if cur_time == datetime.datetime.combine(DATE[d], datetime.time(9, 41, 35)):
                        pass

                    # Определение какие события перешли в задачи
                    check_incoming_application_flow(cur_time)

                    # Изменение статусов задач: входящий/пропущенный, длительность дозвона, приоритет и группа, если
                    # появился второй необработанный пропущенный с одного номера, то первый пропущенный "не активный"
                    update_tasks(cur_time, d)

                    # Завершение действий операторов, проставление времен, изменение статусов задач,
                    # изменение статусов операторов
                    end_actions(cur_time, d, oc)

                    # По всем активным задачам пройтись: выбрать задачу, определить доступна ли группа, создать
                    # действие, заполнить действие, изменить статус задачи, если есть еще необработанный пропущенный с
                    # одного номера, то этот пропущенный уходит в архив

                    assign_tasks(cur_time, oc)
                    # Если есть операторы в предобработке, то прерывать оператора, если есть входящий и
                    # заново начинать новую задачу

                    try:
                        cur_time = min([model.useful_points[model.useful_points['Дата и время'] > cur_time].iloc[0][
                                            'Дата и время'],
                                        end_point if model.actions[model.actions['Начало звонка'] > cur_time].empty else
                                        model.actions[model.actions['Начало звонка'] > cur_time]['Начало звонка'].min(
                                            skipna=True),
                                        end_point if pd.isnull(
                                            model.operators[model.operators['Статус'] != 'Свободен']
                                            ['Время ближайшего освобождения'].min(skipna=True))
                                        else model.operators[model.operators['Статус'] != 'Свободен']
                                        ['Время ближайшего освобождения'].min(skipna=True),

                                        datetime.datetime.combine(DATE[d], datetime.time(cur_time.hour + 1, 0, 0))])
                    except IndexError:
                        cur_time = end_point
                    print(cur_time, datetime.datetime.now() - a2)

                while not model.operators[model.operators['Статус'] != 'Свободен'].empty:
                    a2 = datetime.datetime.now()
                    # Завершение действий операторов, проставление времен, изменение статусов задач,
                    # изменение статусов операторов
                    end_actions(cur_time, d, oc)

                    try:
                        cur_time = end_point if model.operators[model.operators['Статус'] != 'Свободен'].empty \
                            else (model.operators[model.operators['Статус'] != 'Свободен']
                                  ['Время ближайшего освобождения'].min(skipna=True)
                                  if model.actions[model.actions['Начало звонка'] > cur_time].empty else
                                  min(model.actions[model.actions['Начало звонка'] > cur_time]['Начало звонка'].min(
                                      skipna=True),
                                      model.operators[model.operators['Статус'] != 'Свободен']
                                      ['Время ближайшего освобождения'].min(skipna=True)))
                    except IndexError:
                        cur_time = end_point
                    print(cur_time, datetime.datetime.now() - a2)

                # Сбор статистики

                a3 = datetime.datetime.now()
                update_tasks_cur(model.incoming_application_flow, 'Входные данные')
                update_tasks_cur(model.tasks, 'Задачи')
                update_tasks_cur(model.classifier, 'Классификатор')
                update_tasks_cur(model.actions, 'Действия')
                a4 = datetime.datetime.now()

                print('Загрузка входных данных: ', a1 - a0)
                print('Выполнение процесса: ', a3 - a1)
                print('Запись результатов: ', a4 - a3)
                model.tasks['Ожидание'] = model.tasks['Ожидание'].astype(int)

                model.get_new_statistic(start_point, end_point, oc)
                update_tasks_cur(model.statistic, 'Выходные параметры (новые)')
                save_day(DATE[d], OPERATOR_COUNT[oc], 'жм1.5')
