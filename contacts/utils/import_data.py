import pandas as pd


class ImportData:
    def __init__(self, file_path, extension):
        self.file_path = file_path
        self.extension = extension
        self.columns_map = {
            'ID': 'contact_ID',
            'Фамилия': 'contact_LAST_NAME',
            'Имя': 'contact_NAME',
            'Отчество': 'contact_SECOND_NAME',
            'Email': 'contact_EMAIL',
            'Телефон': 'contact_PHONE',
            'Компания': 'company_TITLE'
        }

    def parse(self):
        if self.extension == '.csv':
            df = pd.read_csv(self.file_path, encoding='utf-8-sig')

        else:
            df = pd.read_excel(self.file_path, engine='openpyxl')

        df.fillna('', inplace=True)

        df.rename(columns=self.columns_map, inplace=True)

        df = df[[v for v in self.columns_map.values()]]

        return df.to_dict(orient='records')