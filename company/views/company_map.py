import hashlib
import logging
import os

import requests
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from dotenv import load_dotenv

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth


load_dotenv()

logger = logging.getLogger('bitrix')

COMPANY_ENTITY_TYPE_ID = '4'
REQUEST_TIMEOUT = 10
GEOCODE_CACHE_SECONDS = 60 * 60 * 24 * 30


def get_geocode(company):
    address = ' '.join(filter(None, [
        company.get('COUNTRY'),
        company.get('PROVINCE'),
        company.get('REGION'),
        company.get('CITY'),
        company.get('ADDRESS_1')
    ]))
    if not address:
        return None

    cache_key = 'geocode:' + hashlib.sha256(address.encode('utf-8')).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        response = requests.get('https://geocode-maps.yandex.ru/v1/', params={
            'apikey': os.environ['YANDEX_API_KEY'],
            'geocode': address,
            'format': 'json',
        }, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        members = response.json()['response']['GeoObjectCollection']['featureMember']
        position = members[0]['GeoObject']['Point']['pos']
        point = [float(geocode) for geocode in position.split(' ')[::-1]]
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        # Текст ошибки requests содержит URL с ключом, поэтому в лог пишем только тип
        logger.warning('Geocoding failed: %s', type(e).__name__)
        return None

    cache.set(cache_key, point, GEOCODE_CACHE_SECONDS)
    return point


def get_logo(company):
    download_url = (company.get('LOGO') or {}).get('downloadUrl')
    if not download_url:
        return None

    bitrix_domain = os.environ['BITRIX_DOMAIN']
    root_url = os.environ['ROOT_URL'].rstrip('/')
    full_url = f'https://{bitrix_domain}{download_url}'

    logo_dir = os.path.join(settings.MEDIA_ROOT, 'company_logos')
    os.makedirs(logo_dir, exist_ok=True)
    file_name = f"logo_{company['ID']}.png"
    file_path = os.path.join(logo_dir, file_name)

    if not os.path.exists(file_path):
        try:
            response = requests.get(full_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)
        except (requests.RequestException, OSError) as e:
            logger.warning("Logo download failed, id %s: %s", company['ID'], type(e).__name__)
            return None

    media_url = '/' + settings.MEDIA_URL.strip('/') + '/'
    return f'{root_url}{media_url}company_logos/{file_name}'


def get_company_id(address):
    if str(address.get('ANCHOR_TYPE_ID')) == COMPANY_ENTITY_TYPE_ID:
        return str(address.get('ANCHOR_ID'))
    if str(address.get('ENTITY_TYPE_ID')) == COMPANY_ENTITY_TYPE_ID:
        return str(address.get('ENTITY_ID'))
    return None


@main_auth(on_cookies=True)
def company_map(request):
    but = request.bitrix_user_token

    companies = but.call_list_method('crm.company.list', {'select': ['ID', 'TITLE', 'LOGO']})
    companies = {str(company['ID']): company for company in companies}

    addresses = {}
    for address in but.call_list_method('crm.address.list'):
        company_id = get_company_id(address)
        if company_id in companies:
            addresses.setdefault(company_id, address)

    points = []
    for company_id, address in addresses.items():
        geocode = get_geocode(address)
        if geocode is None:
            continue
        points.append({
            'TITLE': companies[company_id]['TITLE'],
            'GEOCODE': geocode,
            'logoURL': get_logo(companies[company_id]),
        })

    return render(request, 'company_map.html', {
        'points': points,
        'yandex_maps_js_key': os.environ['YANDEX_MAPS_JS_KEY'],
    })
