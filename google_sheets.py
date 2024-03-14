import pandas as pd
import pygsheets

from constants import DATE, GS_NAME


def get_matrices():
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title('Матрицы')

        # Матрица групп (аналог цветов), Матрица приоритетов, Матрица вероятности дозвона, Матрица конверсии в запись
        values = wks.get_values_batch(ranges=['A3:J17', 'A21:J35', 'A39:J53', 'A76:J90'])
        return values
    except Exception as e:
        print('Error "Проблема при чтении матриц настроек" ', str(e))
        return None


def get_break_schedule():
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title('График перерывов КЦ')
        df = pd.DataFrame(wks.get_all_records())
        df.head()
        return df
    except Exception as e:
        print('Error "Проблема при чтении графика перерывов КЦ" ', str(e))
        return None


def get_available_groups():
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title('Матрица доступных групп')
        df = pd.DataFrame(wks.get_all_records())
        df.head()
        return df
    except Exception as e:
        print('Error "Проблема при чтении матрицы доступных групп по времени" ', str(e))
        return None


def get_IDENT_telephony():
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title('Телефония: ' + DATE.strftime('%d.%m.%Y'))
        df = pd.DataFrame(wks.get_all_records())
        df.head()
        df['Дата и время'] = pd.to_datetime(df['Дата и время'], format='%d.%m.%Y %H:%M:%S')
        df = df.sort_values('Дата и время')
        df = df.loc[df['Входящий'] != ""]
        return df
    except Exception as e:
        print('Error "Проблема при чтении телефонии из IDENT" ', str(e))
        return None
