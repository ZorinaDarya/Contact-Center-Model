from constants import PATIENT_WAITING, DURATION_INCOMING_CALL


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


# def wait_classification(row):
#     if 0 <= row['Ожидание'] < 5:
#         val = '0 - 5'
#     elif 5 <= row['Ожидание'] < 20:
#         val = '5 - 20'
#     else:
#         val = '20+'
#
#     return val


def call_number_classification(row):

    return ''


def type_classification(row, ident):
    try:
        ident_type = ident[((ident['Телефон'] == row['Телефон']) &
                           (ident['Дата и время'] <= row['Дата и время']) &
                            (ident['Ожидание'] == row['Ожидание']) &
                            (ident['Длительность'] == row['Разговор']))].iloc[0]['Тип']
    except IndexError as e:
        print('-----------------------------------------')
        print('Warning "Не нашлось такого звонка в IDENT"\n', row, str(e))
        ident_type = 'Хочет записаться.'
    return ident_type




