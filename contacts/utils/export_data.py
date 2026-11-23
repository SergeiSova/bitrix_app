import io
import os
import re
import tempfile

import pandas as pd

from django.conf import settings
from django.http import FileResponse


FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')
PHONE_LIKE = re.compile(r'[+\d\s()\-]+')


def neutralize_formula(value):
    """Не дать Excel выполнить значение из CRM как формулу. Телефоны не меняются."""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES) and not PHONE_LIKE.fullmatch(value):
        return "'" + value
    return value


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
        self.df = self.df.apply(lambda column: column.map(neutralize_formula))
        self.export_dir = os.path.join(settings.BASE_DIR, 'temp', 'contact_export')
        self.file_path = None

        os.makedirs(self.export_dir, exist_ok=True)

    def _temp_path(self, suffix):
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=self.export_dir)
        temp.close()
        return temp.name

    def export_csv(self):
        self.file_path = self._temp_path('.csv')
        self.df.to_csv(self.file_path, index=False, encoding='utf-8-sig')
        return self._make_response('contact_export.csv')

    def export_xlsx(self):
        self.file_path = self._temp_path('.xlsx')
        self.df.to_excel(self.file_path, index=False, engine='openpyxl')
        return self._make_response('contact_export.xlsx')

    def _make_response(self, filename):
        try:
            with open(self.file_path, 'rb') as exported:
                content = io.BytesIO(exported.read())
        finally:
            os.remove(self.file_path)
        return FileResponse(content, as_attachment=True, filename=filename)
