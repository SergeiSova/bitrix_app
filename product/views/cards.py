import os

from django.http import HttpResponse
from django.shortcuts import render
from dotenv import load_dotenv

from integration_utils.bitrix24.bitrix_token import BitrixToken
from integration_utils.bitrix24.exceptions import BitrixApiError

from product.models import QRLink


load_dotenv()

def product_card(request, uuid):

    try:
        relation = QRLink.objects.get(unique_id=uuid)
    except Exception as e:
        return  render(request, "dummy_mode.html")

    product_id = relation.product_id

    try:
        bitrix_domain = os.environ['BITRIX_DOMAIN']
        bitrix_webhook_auth = os.environ['BITRIX_WEBHOOK_AUTH']

        webhook_token = BitrixToken(
            domain=bitrix_domain,
            web_hook_auth=bitrix_webhook_auth
        )

        product_data = webhook_token.call_api_method(
            "crm.product.get",
            {"id": product_id})['result']

        if not product_data:
            return HttpResponse("Не удалось найти такой товар.", status=404)

        photo_data = webhook_token.call_api_method(
            "catalog.productImage.list",
            params={
                "productId": product_id,
                "select": ["detailUrl"]
            }
        )['result']['productImages']

        if photo_data:
            image = photo_data[0]['detailUrl']
        else:
            image = None

    except BitrixApiError:
        return HttpResponse("Ошибка при обращении к Битриксу. Не удалось загрузить товар", status=500)

    return render(request, "card_mode.html", {'product': product_data, 'image_url': image})