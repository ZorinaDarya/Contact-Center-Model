from comagic import get_telephony
from google_sheets import get_matrices, get_break_schedule, get_available_groups
from data_transformation import matrix_to_df, available_groups_matrix_to_df, input_data_classification
from models import Model


def init_matrices():
    values = get_matrices()
    df = matrix_to_df(values)
    return df


def init_available_groups_matrix():
    values = get_available_groups()
    df = available_groups_matrix_to_df(values)
    return df


def init_input_data():
    values = get_telephony()
    df = input_data_classification(values)
    return df


def init_model():
    classifier = init_matrices()
    schedule = get_break_schedule()
    available_groups = init_available_groups_matrix()
    input_data = init_input_data()

    model = Model(input_data, classifier, available_groups, schedule)

    return model
