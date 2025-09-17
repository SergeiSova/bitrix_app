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
        product_name = request.POST.get('product_name', '').strip()

        print(f"DEBUG: Received product_name = '{product_name}'")  # Отладка

        # Проверка заполнения поля
        if not product_name:
            error_message = "Введите название товара"
            print("DEBUG: Empty product_name, showing error")

        else:
            try:
                print(f"DEBUG: Searching for product: '{product_name}'")

                # Поиск товара по названию (точное совпадение)
                products = but.call_api_method("crm.product.list", {
                    'filter': {'NAME': product_name},
                    'select': ['ID', 'NAME']
                })['result']

                print(f"DEBUG: Found {len(products)} products with exact match")

                if not products:
                    # Если не найдено точное совпадение, пробуем поиск по вхождению
                    products = but.call_api_method("crm.product.list", {
                        'filter': {'?NAME': product_name},
                        'select': ['ID', 'NAME']
                    })['result']

                    print(f"DEBUG: Found {len(products)} products with partial match")

                if not products:
                    error_message = f"Товар с названием '{product_name}' не найден"
                    print("DEBUG: No products found")
                else:
                    # Берем первый найденный товар
                    product = products[0]
                    product_id = int(product['ID'])
                    product_full_name = product['NAME']

                    print(f"DEBUG: Selected product: ID={product_id}, Name='{product_full_name}'")

                    # Генерация QR-кода
                    try:
                        root_url = os.environ.get('ROOT_URL', 'http://localhost:8000/')

                        # Создаем запись в БД
                        qr_link = QRLink.objects.create(product_id=product_id)
                        uuid = str(qr_link.unique_id)
                        gen_url = root_url + "/product/card/" + uuid

                        print(f"DEBUG: Generated URL: {gen_url}")

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
                            "product_name": product_full_name,
                            "gen_url": gen_url,
                            "qr_base64": qr_base64
                        }

                        print("DEBUG: QR code generated successfully")

                    except Exception as e:
                        error_message = f"Ошибка при генерации QR-кода: {str(e)}"
                        print(f"DEBUG: QR generation error: {e}")

            except BitrixApiError as e:
                error_message = "Ошибка при обращении к Bitrix24. Проверьте подключение к системе"
                print(f"DEBUG: Bitrix API error: {e}")
            except Exception as e:
                error_message = f"Неожиданная ошибка: {str(e)}"
                print(f"DEBUG: Unexpected error: {e}")

    # Возвращаем шаблон с данными об ошибке или успехе
    context = {
        'error_message': error_message,
        'form_data': {
            'product_name': request.POST.get('product_name', '') if request.method == 'POST' else ''
        }
    }

    # Добавляем данные успешной генерации, если есть
    if success_data:
        context.update(success_data)

    print(f"DEBUG: Rendering template with context: error='{error_message}', success={bool(success_data)}")

    return render(request, "generator_mode.html", context)