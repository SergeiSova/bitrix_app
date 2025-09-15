from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
import logging
@main_auth(on_cookies=True)
def add_deal(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        stage_id = request.POST.get("stage_id", "").strip()
        title = request.POST.get("title", "").strip()
        opportunity = request.POST.get("opportunity", "0").strip()
        begindate = request.POST.get("begindate", "").strip()
        closedate = request.POST.get("closedate", "").strip()
        address = request.POST.get("address", "").strip()
        try:
            opportunity_value = float(opportunity)
        except (ValueError, TypeError):
            opportunity_value = 0.0
        fields = {
            'STAGE_ID': stage_id,
            'TITLE': title,
            'OPPORTUNITY': opportunity_value,
            'BEGINDATE': begindate,
            'CLOSEDATE': closedate,
            'UF_CRM_1757887195': address,  # адрес доставки
        }
        try:
            bitrix = request.bitrix_user_token
            result = bitrix.call_api_method('crm.deal.add', {'fields': fields})
            logging.info(f"Сделка добавлена: {result}")
        except Exception as e:
            logger = logging.getLogger('bitrix')
            logger.error(f"Ошибка при добавлении сделки: {e}")
        return redirect('deals')
    return render(request, 'add_mode.html')