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

    # Инициализация переменных для шаблона
    error_message = None
    success_data = {}

    if request.method == 'POST':
        product_id = request.POST.get('product_id', '').strip()
        product_name = request.POST.get('product_name', '').strip()

        # Проверка заполнения полей
        if not product_id and not product_name:
            error_message = "Заполните хотя бы одно поле"

        else:
            try:
                # Обработка по ID
                if product_id:
                    try:
                        product_id = int(product_id)
                    except ValueError:
                        error_message = "Некорректный ID товара"

                    if not error_message:
                        try:
                            product_data = but.call_api_method(
                                "crm.product.get",
                                {"id": product_id})

                            if "result" not in product_data or not product_data["result"]:
                                error_message = "Продукт с таким ID не найден в Битриксе"
                        except BitrixApiError:
                            error_message = "Ошибка при обращении к Битриксу. Возможно товара с данным ID не существует"

                # Обработка по названию
                elif product_name:
                    try:
                        products = but.call_api_method("crm.product.list", {
                            'filter': {'NAME': product_name},
                            'select': ['ID']
                        })['result']

                        if not products:
                            error_message = "Не удалось найти товар с таким названием"
                        else:
                            product_id = int(products[0]['ID'])
                    except BitrixApiError:
                        error_message = "Ошибка при обращении к Bitrix24"

                # Генерация QR-кода, если нет ошибок
                if not error_message:
                    try:
                        root_url = os.environ.get('ROOT_URL', 'http://localhost:8000/')

                        # Создаем запись в БД
                        qr_link = QRLink.objects.create(product_id=product_id)
                        uuid = str(qr_link.unique_id)
                        gen_url = root_url + "/product/card/" + uuid

                        # Генерируем QR-код
                        qr_img = qrcode.make(gen_url)
                        buffer = io.BytesIO()
                        qr_img.save(buffer, format="PNG")
                        img_bytes = buffer.getvalue()
                        buffer.close()

                        qr_base64 = base64.b64encode(img_bytes).decode('utf-8')

                        # Данные для успешного отображения
                        success_data = {
                            "product_id": product_id,
                            "gen_url": gen_url,
                            "qr_base64": qr_base64
                        }

                    except Exception as e:
                        error_message = f"Ошибка при генерации QR-кода: {str(e)}"

            except Exception as e:
                error_message = f"Неожиданная ошибка: {str(e)}"

    # Возвращаем шаблон с данными об ошибке или успехе
    context = {
        'error_message': error_message,
        'form_data': {
            'product_id': request.POST.get('product_id', '') if request.method == 'POST' else '',
            'product_name': request.POST.get('product_name', '') if request.method == 'POST' else ''
        }
    }

    # Добавляем данные успешной генерации, если есть
    if success_data:
        context.update(success_data)

    return render(request, "generator_mode.html", context)