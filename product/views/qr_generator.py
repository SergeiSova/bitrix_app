import os  # Работа с переменными окружения
import qrcode  # Библиотека для генерации QR-кодов
import io  # Работа с потоками ввода/вывода в памяти
import base64  # Кодирование/декодирование в base64

from django.shortcuts import render  # Функция render для рендеринга шаблонов

from dotenv import load_dotenv  # Загрузка переменных окружения из .env-файла

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth  # Декоратор для аутентификации пользователя в Bitrix24
from integration_utils.bitrix24.exceptions import BitrixApiError  # Исключение при ошибках API Bitrix24

from product.models import QRLink  # Модель для хранения связи QR-кода и товара

# Загружаем переменные окружения из .env
load_dotenv()


# Декоратор для аутентификации на основе cookies
@main_auth(on_cookies=True)
def qr_generator(request):

    # Получаем токен пользователя Bitrix24 из запроса
    but = request.bitrix_user_token

    # Инициализация переменных для шаблона
    error_message = None
    success_data = {}

    if request.method == 'POST':
        # Получаем название товара из формы и убираем лишние пробелы
        product_name = request.POST.get('product_name', '').strip()

        # Отладочный вывод: полученное название товара
        print(f"DEBUG: Received product_name = '{product_name}'")  # Отладка

        # Проверка заполнения поля
        if not product_name:
            error_message = "Введите название товара"
            print("DEBUG: Empty product_name, showing error")
        else:
            try:
                # Отладочный вывод: начало поиска товара
                print(f"DEBUG: Searching for product: '{product_name}'")

                # Поиск товара по названию (точное совпадение)
                products = but.call_api_method("crm.product.list", {
                    'filter': {'NAME': product_name},
                    'select': ['ID', 'NAME']
                })['result']

                # Отладочный вывод: количество найденных товаров с точным совпадением
                print(f"DEBUG: Found {len(products)} products with exact match")

                if not products:
                    # Если не найдено точное совпадение, пробуем поиск по вхождению
                    products = but.call_api_method("crm.product.list", {
                        'filter': {'?NAME': product_name},
                        'select': ['ID', 'NAME']
                    })['result']

                    # Отладочный вывод: количество найденных товаров с частичным совпадением
                    print(f"DEBUG: Found {len(products)} products with partial match")

                if not products:
                    # Если ничего не найдено — ошибка
                    error_message = f"Товар с названием '{product_name}' не найден"
                    print("DEBUG: No products found")
                else:
                    # Берем первый найденный товар
                    product = products[0]
                    product_id = int(product['ID'])
                    product_full_name = product['NAME']

                    # Отладочный вывод: выбранный товар
                    print(f"DEBUG: Selected product: ID={product_id}, Name='{product_full_name}'")

                    # Генерация QR-кода
                    try:
                        # Получаем корневой URL из переменных окружения (по умолчанию локальный)
                        root_url = os.environ.get('ROOT_URL', 'http://localhost:8000/')

                        # Создаем запись в БД для связи QR и товара
                        qr_link = QRLink.objects.create(product_id=product_id)
                        uuid = str(qr_link.unique_id)

                        # Формируем URL для карточки товара
                        gen_url = root_url + "/product/card/" + uuid

                        # Отладочный вывод: сгенерированный URL
                        print(f"DEBUG: Generated URL: {gen_url}")

                        # Генерируем QR-код на основе URL
                        qr_img = qrcode.make(gen_url)
                        buffer = io.BytesIO()
                        qr_img.save(buffer, format="PNG")
                        img_bytes = buffer.getvalue()
                        buffer.close()

                        # Кодируем изображение в base64 для вставки в HTML
                        qr_base64 = base64.b64encode(img_bytes).decode('utf-8')

                        # Данные для успешного отображения в шаблоне
                        success_data = {
                            "product_id": product_id,
                            "product_name": product_full_name,
                            "gen_url": gen_url,
                            "qr_base64": qr_base64
                        }

                        # Отладочный вывод: успешная генерация QR
                        print("DEBUG: QR code generated successfully")

                    except Exception as e:
                        # Ошибка при генерации QR-кода
                        error_message = f"Ошибка при генерации QR-кода: {str(e)}"
                        print(f"DEBUG: QR generation error: {e}")

            except BitrixApiError as e:
                # Ошибка при обращении к API Bitrix24
                error_message = "Ошибка при обращении к Bitrix24. Проверьте подключение к системе"
                print(f"DEBUG: Bitrix API error: {e}")

            except Exception as e:
                # Неожиданная ошибка
                error_message = f"Неожиданная ошибка: {str(e)}"
                print(f"DEBUG: Unexpected error: {e}")

    # Формируем контекст для шаблона
    context = {
        'error_message': error_message,
        'form_data': {
            'product_name': request.POST.get('product_name', '') if request.method == 'POST' else ''
        }
    }

    # Добавляем данные успешной генерации, если есть
    if success_data:
        context.update(success_data)

    # Отладочный вывод: рендеринг шаблона
    print(f"DEBUG: Rendering template with context: error='{error_message}', success={bool(success_data)}")

    # Рендерим шаблон с контекстом
    return render(request, "generator_mode.html", context)
