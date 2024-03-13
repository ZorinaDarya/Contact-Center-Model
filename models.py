import pandas as pd


class IncomingCall:

    def __init__(self, id, start_at, pat_phone, cc_phone, category, wait, talk):
        self.title = title
        self.description = description

    def __iter__(self):
        for attr_name in self.__dict__:
            yield getattr(self, attr_name)


if __name__ == '__main__':

    site_1 = URL_2(title='Купить телевизор', description='Телевизоры по низкой цене')
    site_2 = URL_2(title='Услуги юриста', description='Адвокат спешит к вам')

    df = pd.DataFrame([site_1, site_2])
    df.columns = site_1.__dict__
    print(df)