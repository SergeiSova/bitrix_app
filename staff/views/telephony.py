import random
import datetime

from django.utils import timezone
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from integration_utils.bitrix24.models import BitrixUserToken


def generate_phone_number():
    return '+79' + ''.join([str(random.randint(0, 9)) for _ in range(9)])


@csrf_exempt
def call_generator(request):
    but = BitrixUserToken.objects.filter(user__is_admin=True).last()

    user_result = but.call_list_method('user.get',{'FILTER': {'ACTIVE': 'Y'}})
    user_ids = [user['ID'] for user in user_result]

    if request.method == 'POST':
        now = timezone.now()

        for _ in range(10):
            user_id = int(random.choice(user_ids))
            duration = random.randint(0, 300)

            call_start = now - datetime.timedelta(days=random.randint(0, 2))
            call = but.call_list_method('telephony.externalcall.register', {
                'USER_ID': user_id,
                'PHONE_NUMBER': generate_phone_number(),
                "CALL_START_DATE": call_start.isoformat(),
                "TYPE": 1,
            })

            call_id = call.get("CALL_ID")
            if not call_id:
                continue

            but.call_list_method('telephony.externalcall.finish', {
                'CALL_ID': call_id,
                'USER_ID': user_id,
                'DURATION': duration,
                "STATUS_CODE": "200",
            })

    return redirect("telephony")