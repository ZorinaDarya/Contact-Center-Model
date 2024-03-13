import numpy as np
from pandas import DataFrame

from markup_functions import call_number_classification, type_classification, wait_calculation, \
    talk_calculation


def matrix_to_df(matrices):
    matrix = matrices[0]
    df = DataFrame(columns=['Направление', 'Тип', 'Длительность дозвона', 'Номер звонка', 'Начало', 'Конец',
                            'Приоритет', 'Группа', 'Вероятность дозвона', 'Конверсия'])

    for i in ['Пропущенный', 'Входящий', 'Исходящий']:
        if i == 'Исходящий':
            row = [i, '', '', '', '', '', matrices[0][2][9], matrices[1][2][9], matrices[2][2][9], matrices[3][2][9]]
            df.loc[len(df.index)] = row
        else:
            for j in range(3, len(matrix)):
                if i == 'Входящий':
                    row = [i, matrix[j][0], matrix[j][1], matrix[j][2], '', '',
                         matrices[0][j][3], matrices[1][j][3], matrices[2][j][3], matrices[3][j][3]]
                    df.loc[len(df.index)] = row
                else:
                    for start, end, k in zip(matrix[1][4:9], matrix[2][4:9],
                                             [i for i in range(4, 4 + len(matrix[1][4:9]))]):
                        row = [i, matrix[j][0], matrix[j][1], matrix[j][2], start, end,
                             matrices[0][j][k], matrices[1][j][k], matrices[2][j][k], matrices[3][j][k]]
                        df.loc[len(df.index)] = row

    return df


def available_groups_matrix_to_df(df):
    column_name = 'Интервал'
    df.insert(loc=0, column='Начало', value=df[column_name].str.extract(r'(^\d+)'))
    df.insert(loc=1, column='Конец', value=df[column_name].str.extract(r' (\d+)'))

    del df[column_name]

    return df


def input_data_classification(df):
    df['Ожидание'] = df.apply(wait_calculation, axis=1)
    df['Разговор'] = df.apply(talk_calculation, axis=1)

    df['Тип'] = df.apply(type_classification, axis=1)
    df['Номер звонка'] = df.apply(call_number_classification, axis=1)

    return df

