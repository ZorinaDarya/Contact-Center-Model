import datetime
import requests
from pandas import DataFrame

from constants import DATE, PRE_CALL


def login():
    params = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "login.user",
        "contentType": "application/json",
        "params": {
            "login": "renident.marketing@stomodomo.ru",
            "password": "domostomo2019"
        }
    }
    response = requests.post("https://dataapi.comagic.ru/v2.0", json=params)
    access_token = response.json()["result"]["data"]["access_token"]
    return access_token


def get_calls(access_token):
    start = str(DATE - datetime.timedelta(days=1)) + ' 21:00:00'
    end = str(DATE) + ' 21:00:00'
    payload = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "get.calls_report",
        "params": {
            "limit": 10000,
            "access_token": access_token,
            "date_from": start,
            "date_till": end,
            "fields": [
                "id",
                "start_time",
                "direction",
                "contact_phone_number",
                "wait_duration",
                "talk_duration",
                "virtual_phone_number",
                "last_answered_employee_full_name"
            ],
            "sort": [
                {
                    "field": "start_time",
                    "order": "asc"
                }
            ]
        }
    }
    response = requests.post("https://dataapi.comagic.ru/v2.0", json=payload)
    calls = response.json()["result"]["data"]
    return calls


def get_message(access_token):
    start = str(DATE - datetime.timedelta(days=1)) + ' 21:00:00'
    end = str(DATE) + ' 21:00:00'
    payload = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "get.offline_messages_report",
        "params": {
            "limit": 10000,
            "access_token": access_token,
            "date_from": start,
            "date_till": end,
            "fields": [
                "id",
                "date_time",
                "visitor_phone_number",
                "group_id"
            ],
            "sort": [
                {
                    "field": "date_time",
                    "order": "asc"
                }
            ]
        }
    }
    messages = requests.post("https://dataapi.comagic.ru/v2.0", json=payload)
    calls = messages.json()["result"]["data"]
    return calls


def get_telephony():
    access_token = login()
    calls = get_calls(access_token)
    messages = get_message(access_token)

    df = DataFrame(columns=['Тип события', 'ID', 'Дата и время', 'Телефон', 'Ожидание', 'Разговор'])

    for i in range(len(calls)):
        if calls[i]["direction"] == "in" and not calls[i]["virtual_phone_number"] in PRE_CALL:
            row = ["Пропущен" if calls[i]["last_answered_employee_full_name"] is None or calls[i]["talk_duration"] == 0
                   else "Взят",
                   int(calls[i]["id"]),
                   datetime.datetime.strptime(calls[i]["start_time"], '%Y-%m-%d %H:%M:%S'),
                   int(calls[i]["contact_phone_number"]),
                   int(calls[i]["wait_duration"]),
                   int(calls[i]["talk_duration"])]
            df.loc[len(df.index)] = row

    for i in range(len(messages)):
        row = ["Заявка",
               int(messages[i]["id"]),
               datetime.datetime.strptime(messages[i]["date_time"], '%Y-%m-%d %H:%M:%S'),
               int(messages[i]["visitor_phone_number"]),
               0, 0]
        df.loc[len(df.index)] = row

    df = df.sort_values('Дата и время')

    return df
