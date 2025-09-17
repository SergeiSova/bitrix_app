import os
import tempfile

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from integration_utils.bitrix24.functions.batch_api_call import _batch_api_call

from utils.import_data import ImportData


ALLOWED_EXTENSIONS = ['.csv', '.xlsx']

@main_auth(on_cookies=True)
def import_contacts(request):
    but = request.bitrix_user_token

    if request.method == 'POST':
        uploaded_file = request.FILES.get('fileUpload')

        if uploaded_file:

            _, ext = os.path.splitext(uploaded_file.name)
            if ext.lower() not in ALLOWED_EXTENSIONS:
                return HttpResponse('Ошибка: поддерживаются только .csv и .xlsx файлы.')

            temp_dir = os.path.join(settings.BASE_DIR, 'temp', 'contact_import')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=ext,
                dir=temp_dir,
                mode='wb'
            )

            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

            temp_file_path = temp_file.name
            temp_file.close()
            imported = ImportData(temp_file_path, ext)
            data_list = imported.parse()

            companies = but.call_list_method('crm.company.list', {'select':['ID','TITLE']})
            companies = {company['TITLE']: company for company in companies}

            contact_data_add = []
            for data in data_list:
                if data['company_TITLE'] in list(companies.keys()):
                    data['company_ID'] = companies[data['company_TITLE']]['ID']
                else:
                    company_id = but.call_list_method('crm.company.add', {'fields': {'TITLE': data['company_TITLE']}})
                    data['company_ID'] = company_id

                if data['contact_ID'] == '':
                    contact_data_add.append(data)

            batch = []
            for idx, contact in enumerate(contact_data_add, start=1):
                fields ={
                    'NAME': contact.get('contact_NAME', ''),
                    'SECOND_NAME': contact.get('contact_SECOND_NAME', ''),
                    'LAST_NAME': contact.get('contact_LAST_NAME', ''),
                    'PHONE': [{'VALUE': contact.get('contact_PHONE', ''),
                               'VALUE_TYPE': "WORK"}],
                    'EMAIL': [{'VALUE': contact.get('contact_EMAIL', ''),
                               'VALUE_TYPE': "WORK"}],
                    'COMPANY_ID': contact.get('company_ID', ''),
                }

                batch.append((
                    f"contact_{idx}",
                    "crm.contact.add",
                    {"fields": fields}
                ))

            add_result = _batch_api_call(
                methods=batch,
                bitrix_user_token=but,
                function_calling_from_bitrix_user_token_think_before_use=True)



            try:
                os.remove(temp_file_path)
                print(f"[ExportFile] Файл удалён: {temp_file_path}")
            except Exception as e:
                print(f"[ExportFile] Ошибка при удалении: {e}")


        else:
            return HttpResponse('Произошла ошибка при загрузке файла. Возможно вы не выбрали его.')

    return render(request, 'import_mode.html')