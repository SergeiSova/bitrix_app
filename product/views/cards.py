from django.http import HttpResponse  # Формирование HTTP-ответов
from django.shortcuts import render  # Функция render для рендеринга шаблонов

from dotenv import load_dotenv  # Загрузка переменных окружения из .env-файла

from integration_utils.bitrix24.bitrix_token import BitrixToken  # Класс для работы с API Битрикс24
from integration_utils.bitrix24.exceptions import BitrixApiError  # Исключение при ошибках API Битрикс24

from product.models import QRLink  # Модель для хранения связи QR-кода и товара

# Загружаем переменные окружения из .env
load_dotenv()

from django.conf import settings  # Настройки Django (включая BITRIX_DOMAIN и BITRIX_WEBHOOK_AUTH)


def product_card(request, uuid):

    # Получаем настройки домена и токена из Django settings
    bitrix_domain = settings.BITRIX_DOMAIN
    bitrix_webhook_auth = settings.BITRIX_WEBHOOK_AUTH

    try:
        # Ищем связь QR-кода и товара в базе
        relation = QRLink.objects.get(unique_id=uuid)
    except Exception:
        # Если запись не найдена, показываем заглушку
        return render(request, "dummy_mode.html")

    # Извлекаем ID товара, связанного с найденным QRLink
    product_id = relation.product_id

    try:
        # Инициализируем клиент для вызова методов Битрикс24
        webhook_token = BitrixToken(
            domain=bitrix_domain,
            web_hook_auth=bitrix_webhook_auth
        )

        # Запрашиваем данные товара из CRM
        product_data = webhook_token.call_api_method(
            "crm.product.get",
            {"id": product_id}
        )['result']

        # Если товар не найден — возвращаем 404
        if not product_data:
            return HttpResponse("Не удалось найти такой товар.", status=404)

        # Запрашиваем список фотографий товара (detailUrl)
        photo_data = webhook_token.call_api_method(
            "catalog.productImage.list",
            params={
                "productId": product_id,
                "select": ["detailUrl"]
            }
        )['result']['productImages']

        # Если фото есть — берем URL первого, иначе — None
        if photo_data:
            image = photo_data[0]['detailUrl']
        else:
            image = None

    except BitrixApiError:
        # Если при обращении к API Битрикс24 произошла ошибка
        return HttpResponse(
            "Ошибка при обращении к Битриксу. Не удалось загрузить товар",
            status=500
        )

    # Рендерим страницу с данными товара и URL изображения
    return render(
        request,
        "card_mode.html",
        {
            'product': product_data,
            'image_url': image
        }
    )
