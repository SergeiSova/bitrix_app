import os
import requests
from django.conf import settings
from django.shortcuts import render
from dotenv import load_dotenv

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth


load_dotenv()

def get_geocode(company):
    address = ' '.join(filter(None, [
        company.get('COUNTRY'),
        company.get('PROVINCE'),
        company.get('REGION'),
        company.get('CITY'),
        company.get('ADDRESS_1')
    ]))

    api_key = os.environ['YANDEX_API_KEY']

    response = requests.get(f'https://geocode-maps.yandex.ru/v1/?apikey={api_key}&geocode={address}&format=json').json()
    position = response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
    return [float(geocode) for geocode in position.split(' ')[::-1]]

def get_logo(company):
    bitrix_domain = os.environ['BITRIX_DOMAIN']
    root_url = os.environ['ROOT_URL']
    download_url = company.get('LOGO').get('downloadUrl')
    full_url = f'https://{bitrix_domain}{download_url}'

    logo_dir = os.path.join(settings.MEDIA_ROOT, 'company_logos')
    os.makedirs(logo_dir, exist_ok=True)
    file_path = os.path.join(logo_dir, f'logo_{company['ID']}.png')

    if os.path.exists(file_path):
        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
        return root_url+f'{settings.MEDIA_URL}{relative_path}'.replace('\\', '/')


    try:
        response = requests.get(full_url)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f'Download error, id: {company['ID']}: {e}')

    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
    return root_url + f'{settings.MEDIA_URL}{relative_path}'.replace('\\', '/')

@main_auth(on_cookies=True)
def company_map(request):
    but = request.bitrix_user_token

    companies = but.call_list_method('crm.company.list')
    companies = {company['ID']: company for company in companies}

    addresses = but.call_list_method('crm.address.list')
    addresses = {address['ENTITY_ID']: address for address in addresses}

    points = []
    for company_id, address in addresses.items():
        point = {
            'TITLE': companies[company_id]['TITLE'],
            'GEOCODE': get_geocode(addresses[company_id]),
            'logoURL': get_logo(companies[company_id]),
        }

        points.append(point)
    return render(request, 'company_map.html', {'points': points})