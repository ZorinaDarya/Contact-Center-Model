import time

import pandas as pd
import pygsheets

from constants import DATE, GS_NAME, GROUP_MATRIX


def get_matrices(m):
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title('Матрицы')

        # Матрица групп (аналог цветов), Матрица приоритетов, Матрица вероятности дозвона, Матрица конверсии в запись
        values = wks.get_values_batch(ranges=[GROUP_MATRIX[m], 'A21:J35', 'A39:J53', 'A76:J90', 'A94:J108'])
        return values
    except Exception as e:
        print('Error "Проблема при чтении матриц настроек" ', str(e))
        return None


def get_break_schedule(d):
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title('График перерывов КЦ')
        df = pd.DataFrame(wks.get_all_records())
        df.head()
        for i in range(10):
            df[str(i + 1) + ' начало'] = pd.to_datetime(DATE[d].strftime('%d.%m.%Y ') + df[str(i + 1) + ' начало'],
                                                        format='%d.%m.%Y %H:%M:%S', errors='coerce')
            df[str(i + 1) + ' конец'] = pd.to_datetime(DATE[d].strftime('%d.%m.%Y ') + df[str(i + 1) + ' конец'],
                                                       format='%d.%m.%Y %H:%M:%S', errors='coerce')
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
        df['Понедельник'] = df['Понедельник'].astype(int)
        df['Вторник'] = df['Вторник'].astype(int)
        df['Среда'] = df['Среда'].astype(int)
        df['Четверг'] = df['Четверг'].astype(int)
        df['Пятница'] = df['Пятница'].astype(int)
        df['Суббота'] = df['Суббота'].astype(int)
        df['Воскресенье'] = df['Воскресенье'].astype(int)
        return df
    except Exception as e:
        print('Error "Проблема при чтении матрицы доступных групп по времени" ', str(e))
        return None


def get_IDENT_telephony():
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title('Телефония')
        df = pd.DataFrame(wks.get_all_records())
        df.head()
        df['Дата и время'] = pd.to_datetime(df['Дата и время'], format='%d.%m.%Y %H:%M:%S')
        df = df.sort_values('Дата и время')
        df = df.loc[df['Входящий'] != ""]
        return df
    except Exception as e:
        print('Error "Проблема при чтении телефонии из IDENT" ', str(e))
        return None


def update_tasks_cur(df, sheet_name):
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    try:
        gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
        sh = gc.open(GS_NAME)
        wks = sh.worksheet_by_title(sheet_name)
        wks.set_dataframe(df, (1, 1), encoding='utf-8', fit=True)
    except Exception as e:
        print('Error "Проблема при записи промежуточных данных в таблицу" ', str(e))
        return None


def save_day(d, oc, mode):
    time.sleep(30)
    CREDENTIALS_FILE = 'wa-bot-372214-f479a48fa726.json'
    # try:
    gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)
    sh = gc.open(GS_NAME)
    wks = sh.worksheet_by_title('Конструктор (новый)')
    values = wks.get_all_values()
    print(values)
    sh.add_worksheet(title=d.strftime("%d.%m.%Y") + '_' + str(oc) + '_' + str(mode), rows=167, cols=11)
    wks_to = sh.worksheet_by_title(d.strftime("%d.%m.%Y") + '_' + str(oc) + '_' + str(mode))
    wks_to.update_values_batch(ranges=['A:K'], values=[values], parse=True)
    # except Exception as e:
    #     print('Error "Проблема при копировании данных" ', str(e))
    #     return None
