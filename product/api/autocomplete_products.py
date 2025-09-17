from django.http import JsonResponse
import logging

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from integration_utils.bitrix24.exceptions import BitrixApiError

logger = logging.getLogger('bitrix')


@main_auth(on_cookies=True)
def autocomplete_products(request):
    query = request.GET.get('q', '').strip()

    # Логирование для отладки
    logger.info(f"Autocomplete request: query='{query}'")

    if not query:
        return JsonResponse({"results": []})

    but = request.bitrix_user_token

    try:
        # Попробуем разные варианты фильтра
        response = but.call_api_method("crm.product.list", {
            "filter": {
                "?NAME": query  # Поиск по вхождению в название
            },
            "select": ["ID", "NAME"],
            "order": {"NAME": "ASC"},
            "start": 0
        })

        logger.info(f"Bitrix24 response: {response}")

        items = response.get("result", [])
        results = [{"id": item["ID"], "name": item["NAME"]} for item in items]

        logger.info(f"Found {len(results)} products")

        return JsonResponse({"results": results})

    except BitrixApiError as e:
        logger.error(f"Bitrix24 API error in autocomplete: {e}")

        # Попробуем альтернативный фильтр, если первый не сработал
        try:
            response = but.call_api_method("crm.product.list", {
                "filter": {
                    "NAME": f"%{query}%"  # Альтернативный синтаксис
                },
                "select": ["ID", "NAME"],
                "order": {"NAME": "ASC"},
                "start": 0
            })

            items = response.get("result", [])
            results = [{"id": item["ID"], "name": item["NAME"]} for item in items]

            return JsonResponse({"results": results})

        except Exception as e2:
            logger.error(f"Alternative filter also failed: {e2}")
            return JsonResponse({
                "results": [],
                "error": "Ошибка поиска товаров"
            }, status=500)

    except Exception as e:
        logger.error(f"Unexpected error in autocomplete: {e}")
        return JsonResponse({
            "results": [],
            "error": "Неожиданная ошибка"
        }, status=500)