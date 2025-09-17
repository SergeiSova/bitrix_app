from django.shortcuts import render
from integration_utils.bitrix24.functions.batch_api_call import _batch_api_call
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth

from utils.export_data import ExportData
from utils.data_parsers import client_parser


@main_auth(on_cookies=True)
def export_contacts(request):
    but = request.bitrix_user_token

    if request.method == "POST":
        companies = but.call_list_method('crm.company.list', {'select':['ID', 'TITLE']})
        companies = {company['ID']: company for company in companies}

        filter = {}

        if request.POST.get('export_type') == 'on':
            is_excel = True
        else:
            is_excel = False

        if request.POST.get('created_from'):
            filter['>DATE_CREATE'] = request.POST.get('created_from')

        if request.POST.get('last_active'):
            filter['>LAST_ACTIVITY_TIME'] = request.POST.get('last_active')

        if request.POST.get('company_name'):
            try:
                for company in companies.values():
                    if company.get('TITLE') == request.POST.get('company_name'):
                        company_id = company.get('ID')
                        filter['COMPANY_ID'] = company_id
            except:
                pass

        contacts = but.call_list_method('crm.contact.list', {'filter': filter,
                                                             'select':['ID']})
        contacts = {contact.get('ID'): contact for contact in contacts}

        batch = _batch_api_call(
            methods=[
                *[(f'contact_{id_contact}', 'crm.contact.get', {'ID': id_contact}) for id_contact in contacts],
                *[(f'company_{id_company}', 'crm.company.get', {'ID': id_company}) for id_company in companies],
            ],
            bitrix_user_token=but,
            function_calling_from_bitrix_user_token_think_before_use=True)

        data = client_parser(batch)
        exporter = ExportData(data)

        if is_excel:
            return exporter.export_xlsx()
        else:
            return exporter.export_csv()

    return render(request, 'export_mode.html')