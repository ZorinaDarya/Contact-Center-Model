import datetime

PRE_CALL = {
        '78122140118': 'Героев',
        '78124139079': 'Колпино',
        '78124139117': 'Оптиков',
        '78124139947': 'Кудрово',
        '78124160106': 'Комендантский',
        '78124160251': 'Девяткино',
        '78124160459': 'Парнас'
    }

DURATION_INCOMING_CALL = 240
DURATION_BACK_CALL = 240
DURATION_OUTGOING_CALL = 240

DURATION_PREPROCESSING_INCOMING_CALL = 20
DURATION_PREPROCESSING_BACK_CALL = 30
DURATION_PREPROCESSING_OUTGOING_CALL = 30

DURATION_POSTPROCESSING_INCOMING_CALL = 120
DURATION_POSTPROCESSING_BACK_CALL = 120
DURATION_POSTPROCESSING_OUTGOING_CALL = 120

OPERATOR_WAITING_BACK_CALL = 10
OPERATOR_WAITING_OUTGOING_CALL = 10

# Минимальная длительность ожидания пациента на линии, если фактически звонок был взят.
# Его ожидание было прервано оператором, поэтому брать его фактическое ожидание мы не можем,
# если оно было меньше заданного значения, так как полагаем, что пациент мог ждать на линии еще n секунд,
# если бы оператор не взял трубку.
PATIENT_WAITING = 30

OPERATOR_COUNT = 5

DEADLINE_BACK_CALL = 60 * 5

COUNT_OUTGOING_CALL = 150

AVAILABLE_ACTIONS_SELECTION_MODE = 'TIME'
# AVAILABLE_ACTIONS_SELECTION_MODE = 'FREE_OPERATOR'

DATE = datetime.date(2024, 2, 29)

GS_NAME = 'ТЗ для модели'

# Справка
DURATION_LUNCH = 60 * 30
DURATION_BREAK = 60 * 15
COUNT_LUNCH = 2
COUNT_BREAK = 2

