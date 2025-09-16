from django.shortcuts import render

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from deals.views.active_deals import iso_transform


@main_auth(on_cookies=True)
def product_catalog(request):
    but = request.bitrix_user_token
    product_list = but.call_api_method("crm.product.list", {
        'order': ['ID'],
        'select': ['ID', 'NAME', 'ACTIVE','DATE_CREATE', 'PRICE'],
    })['result']

    for product in product_list:
        product['DATE_CREATE'] = iso_transform(product['DATE_CREATE'])

    return render(request, 'catalog_mode.html',{'products':product_list})