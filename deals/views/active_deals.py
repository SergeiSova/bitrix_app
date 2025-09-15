from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger('bitrix')


def iso_transform(date_str: str) -> str:
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        dt_moscow = dt.astimezone(ZoneInfo('Europe/Moscow'))
        return dt_moscow.strftime('%d-%m-%Y')
    except (ValueError, TypeError):
        return date_str


# Словарь для преобразования системных идентификаторов этапов в читаемые названия
STAGE_NAMES = {
    "NEW": "Новая",
    "PREPARATION": "В обработке",
    "EXECUTING": "В работе",
    "FINAL_INVOICE": "Выставлен счет",
    "WON": "Успешна",
    "LOSE": "Неуспешна",
    "APPLOGY": "Отменена",
}


@main_auth(on_cookies=True)
def active_deals(request: HttpRequest) -> HttpResponse:
    bitrix_token = request.bitrix_user_token
    user_id = bitrix_token.id

    try:
        response = bitrix_token.call_api_method(
            "crm.deal.list",
            {
                'filter': {
                    'ASSIGNED_BY_ID': user_id,
                    "!@STAGE_ID": ["WON", "LOSE", "APPLOGY"],
                },
                'order': {'BEGINDATE': 'ASC'},
                'select': [
                    'ID', 'STAGE_ID', 'TITLE', 'OPPORTUNITY',
                    'BEGINDATE', 'CLOSEDATE', 'UF_CRM_1757887195',
                ],
            }
        )

    except Exception as e:
        logger.error(f"Ошибка при запросе сделок: {e}")
        response = {'result': []}

    deals = response.get('result', [])[:10]

    for deal in deals:
        if deal.get('BEGINDATE'):
            deal['BEGINDATE'] = iso_transform(deal['BEGINDATE'])
        if deal.get('CLOSEDATE'):
            deal['CLOSEDATE'] = iso_transform(deal['CLOSEDATE'])

        # Преобразуем идентификатор этапа в читаемое название
        stage_id = deal.get('STAGE_ID', '')
        deal['STAGE_NAME'] = STAGE_NAMES.get(stage_id, stage_id)

        # Получаем адрес доставки
        deal['ADDRESS'] = deal.get('UF_CRM_1757887195', '—')

        # Форматируем сумму для лучшего отображения
        if 'OPPORTUNITY' in deal and deal['OPPORTUNITY']:
            try:
                deal['OPPORTUNITY'] = float(deal['OPPORTUNITY'])
            except (ValueError, TypeError):
                pass

    return render(request, 'active_mode.html', {
        'recent_active': deals,
    })