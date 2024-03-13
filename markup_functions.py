from constants import PATIENT_WAITING, DURATION_INCOMING_CALL


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

    return 1


def type_classification(row):

    return 1


def wait_calculation(row):
    if row['Тип события'] != 'Взят':
        val = row['Ожидание']
    else:
        val = max(PATIENT_WAITING, row['Ожидание'])

    return val


def talk_calculation(row):
    if row['Тип события'] == 'Взят':
        val = row['Разговор']
    else:
        val = DURATION_INCOMING_CALL

    return val


