import numpy as np
import pandas as pd
from pandas import DataFrame

from google_sheets import get_IDENT_telephony
from markup_functions import type_classification, wait_calculation, talk_calculation


def matrix_to_df(matrices):
    matrix = matrices[0]
    df = DataFrame(columns=['Направление', 'Тип', 'Длительность дозвона', 'Номер звонка', 'Начало', 'Конец',
                            'Группа', 'Приоритет', 'Вероятность дозвона', 'Конверсия'])

    for i in ['Пропущенный', 'Входящий', 'Исходящий']:
        if i == 'Исходящий':
            row = DataFrame([[i, None, None, None, None, None,
                             int(matrices[0][2][9]), int(matrices[1][2][9]),
                             float(matrices[2][2][9].replace(",", ".")), float(matrices[3][2][9].replace(",", "."))]]
                            , columns=df.columns)
            # df.loc[len(df.index)] = row
            df = pd.concat([df, row])
        else:
            for j in range(3, len(matrix)):
                if i == 'Входящий':
                    row = DataFrame([[i, matrix[j][0], None, None, None, None,
                                     int(matrices[0][j][3]), int(matrices[1][j][3]),
                                     float(matrices[2][j][3].replace(",", ".")),
                                     float(matrices[3][j][3].replace(",", "."))]], columns=df.columns)
                    # df.loc[len(df.index)] = row
                    df = pd.concat([df, row])
                else:
                    for start, end, k in zip(matrix[1][4:9], matrix[2][4:9],
                                             [i for i in range(4, 4 + len(matrix[1][4:9]))]):
                        row = DataFrame([[i, matrix[j][0], matrix[j][1], None, float(start), float(end),
                                         int(matrices[0][j][k]), int(matrices[1][j][k]),
                                         float(matrices[2][j][k].replace(",", ".")),
                                         float(matrices[3][j][k].replace(",", "."))]], columns=df.columns)
                        # df.loc[len(df.index)] = row
                        df = pd.concat([df, row])
    df = df.drop_duplicates()
    return df


def available_groups_matrix_to_df(df):
    column_name = 'Интервал'
    df.insert(loc=0, column='Начало', value=df[column_name].str.extract(r'(^\d+)'))
    df.insert(loc=1, column='Конец', value=df[column_name].str.extract(r' (\d+)'))

    del df[column_name]

    return df


def input_data_classification(df):
    df_ident = get_IDENT_telephony()

    df['Тип'] = df.apply(type_classification, axis=1, ident=df_ident)
    df['Номер звонка'] = None
    # df['Длительность дозвона'] = None

    df['Ожидание'] = df.apply(wait_calculation, axis=1)
    df['Разговор'] = df.apply(talk_calculation, axis=1)

    return df
