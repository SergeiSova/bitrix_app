import os, qrcode, io, base64

from django.http import HttpResponse
from django.shortcuts import render
from dotenv import load_dotenv

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from integration_utils.bitrix24.exceptions import BitrixApiError

from product.models import QRLink


load_dotenv()

@main_auth(on_cookies=True)
def qr_generator(request):
    but = request.bitrix_user_token

    if request.method == 'POST':
        product_id = request.POST['product_id']
        product_name = request.POST['product_name']

        if not product_id and not product_name:
            return HttpResponse("Заполните хотя бы одно поле", status=400)

        if product_id:
            try:
                product_id = int(product_id)
            except ValueError:
                return HttpResponse("Некорректный ID", status=400)

            try:
                product_data = but.call_api_method(
                    "crm.product.get",
                    {"id": product_id})

            except BitrixApiError:
                return HttpResponse("Ошибка при обращении к Битриксу. Возможно товара с данный ID не существует", status=500)

            if "result" not in product_data or not product_data["result"]:
                return HttpResponse("Продукт с таким ID не найден в Битриксе", status=404)

        elif product_name:
            try:
                products = but.call_api_method("crm.product.list",{
                        'filter': {'NAME': product_name},
                        'select': ['ID']})['result']

                if not products:
                    return  HttpResponse("Не удалось найти товар с таким названием", status=404)

            except BitrixApiError:
                return HttpResponse("Ошибка при обращении к Bitrix24", status=500)

            product_id = int(products[0]['ID'])

        root_url = os.environ['ROOT_URL']
        QRLink.objects.create(product_id=product_id)
        uuid = str(QRLink.objects.filter(product_id=product_id).last().unique_id)
        gen_url = root_url + "product/card/" + uuid

        qr_img = qrcode.make(gen_url)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        buffer.close()

        qr_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return render(request, "generator_mode.html", {
            "product_id": product_id,
            "gen_url": gen_url,
            "qr_base64": qr_base64
        })
    return render(request, "generator_mode.html")