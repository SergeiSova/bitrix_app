from django.http import JsonResponse

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth


@main_auth(on_cookies=True)
def autocomplete_companies(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({"results": []})

    but = request.bitrix_user_token
    response = but.call_api_method("crm.company.list", {
        "filter": {
            "?TITLE": query
        },
        "select": ["ID", "TITLE"],
        "order": {"NAME": "ASC"},
        "start": 0
    })

    items = response.get("result", [])
    results = [{"id": item["ID"], "title": item["TITLE"]} for item in items]

    return JsonResponse({"results": results})