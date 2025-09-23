import pandas as pd
import chardet


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

    def detect_encoding(self, file_path):
        """Определяет кодировку файла"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Читаем первые 10KB для определения кодировки
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8')

    def parse(self):
        try:
            if self.extension == '.csv':
                # Определяем кодировку автоматически
                encoding = self.detect_encoding(self.file_path)
                print(f"Определена кодировка CSV: {encoding}")

                df = pd.read_csv(self.file_path, encoding=encoding)
            else:
                df = pd.read_excel(self.file_path, engine='openpyxl')

            # Проверяем, что файл не пустой
            if df.empty:
                print("Файл пуст")
                return []

            df.fillna('', inplace=True)

            # Переименовываем колонки (только существующие)
            existing_columns = [col for col in self.columns_map.keys() if col in df.columns]
            df.rename(columns={col: self.columns_map[col] for col in existing_columns}, inplace=True)

            # Выбираем только существующие колонки после переименования
            available_columns = [v for v in self.columns_map.values() if v in df.columns]
            df = df[available_columns]

            # Преобразуем все строковые значения в правильную кодировку
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].apply(lambda x: x.encode('utf-8').decode('utf-8') if isinstance(x, str) else x)

            print(f"Успешно распаршено {len(df)} записей")
            return df.to_dict(orient='records')

        except Exception as e:
            print(f"Ошибка при парсинге файла: {str(e)}")
            return []