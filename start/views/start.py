from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth


@main_auth(on_start=True, set_cookie=True)
def _start_from_portal(request):
    return render(request, 'start_page.html')


@main_auth(on_cookies=True)
def _start_from_cookie(request):
    return render(request, 'start_page.html')


@csrf_exempt
@xframe_options_exempt
def start(request):
    """Первый вход приходит из портала с AUTH_ID, кнопка «В меню» использует cookie."""
    if request.method == 'POST' and request.POST.get('AUTH_ID'):
        return _start_from_portal(request)
    return _start_from_cookie(request)
