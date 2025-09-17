from django.shortcuts import render  # Функция render для рендеринга шаблонов

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth  # Декоратор для аутентификации пользователя в Bitrix24

from deals.views.active_deals import iso_transform  # Функция для преобразования ISO-дат в удобный формат


# Декоратор для аутентификации на основе cookies
@main_auth(on_cookies=True)
def product_catalog(request):

    # Получаем токен пользователя Bitrix24 из запроса
    but = request.bitrix_user_token

    # Запрашиваем список товаров из CRM с сортировкой по ID и выборкой нужных полей
    product_list = but.call_api_method("crm.product.list", {
        'order': ['ID'],
        'select': ['ID', 'NAME', 'ACTIVE', 'DATE_CREATE', 'PRICE'],
    })['result']

    # Проходим по каждому товару и преобразуем дату создания
    for product in product_list:
        product['DATE_CREATE'] = iso_transform(product['DATE_CREATE'])

    # Рендерим страницу с каталогом товаров
    return render(request, 'catalog_mode.html', {'products': product_list})
