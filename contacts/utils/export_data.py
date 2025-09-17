import os
import tempfile
import threading
import pandas as pd

from django.conf import settings
from django.http import FileResponse


class ExportData:
    def __init__(self, data):
        columns_order = {
            'contact_ID': 'ID',
            'contact_LAST_NAME': 'Фамилия',
            'contact_NAME': 'Имя',
            'contact_SECOND_NAME': 'Отчество',
            'contact_EMAIL': 'Email',
            'contact_PHONE': 'Телефон',
            'company_TITLE': 'Компания'
        }

        self.data = data
        self.df = pd.DataFrame(self.data, columns=list(columns_order.keys()))
        self.df.rename(columns=columns_order, inplace=True)
        self.export_dir = os.path.join(settings.BASE_DIR, 'temp', 'contact_export')
        self.file_path = None

        os.makedirs(self.export_dir, exist_ok=True)

    def export_csv(self):
        temp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.csv',
            dir=self.export_dir,
            mode='w',
            newline='',
            encoding='utf-8-sig'
        )

        self.df.to_csv(temp.name, index=False, encoding='utf-8-sig')
        self.file_path = temp.name
        return self._make_response('contact_export.csv')

    def export_xlsx(self):
        temp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.xlsx',
            dir=self.export_dir,
            mode='w',
            newline='',
            encoding='utf-8-sig'
        )
        self.df.to_excel(temp.name, index=False,  engine='openpyxl')
        self.file_path = temp.name
        return self._make_response('contact_export.xlsx')

    def _make_response(self, filename):
        response = FileResponse(open(self.file_path, 'rb'), as_attachment=True, filename=filename)

        def cleanup():
            try:
                os.remove(self.file_path)
                print(f"[ExportFile] Файл удалён: {self.file_path}")
            except Exception as e:
                print(f"[ExportFile] Ошибка при удалении: {e}")

        # Запускаем таймер удаления
        threading.Timer(20.0, cleanup).start()
        return response