import random
import logging
import time

from django.utils import timezone
from django.shortcuts import redirect
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth

logger = logging.getLogger(__name__)

def generate_phone_number():
    return '+79' + ''.join([str(random.randint(0, 9)) for _ in range(9)])

@main_auth(on_cookies=True)
def call_generator(request):
    if request.method == 'POST':
        but = request.bitrix_user_token
        user_result = but.call_list_method('user.get', {'FILTER': {'ACTIVE': 'Y'}})
        user_ids = [user['ID'] for user in user_result]

        now = timezone.now()

        for i in range(5):
            try:
                user_id = int(random.choice(user_ids))
                duration = random.randint(60, 120)

                call_start = now
                call = but.call_api_method('voximplant.statistic.get', {
                    'USER_ID': user_id,
                    'PHONE_NUMBER': generate_phone_number(),
                    "CALL_START_DATE": call_start.isoformat(),
                    "TYPE": 1,
                })

                call_id = call.get("CALL_ID")
                if not call_id:
                    continue

                time.sleep(0.5)
                but.call_api_method('telephony.externalcall.finish', {
                    'CALL_ID': call_id,
                    'USER_ID': user_id,
                    'DURATION': duration,
                    "STATUS_CODE": "200",
                })

                logger.info(f"Successfully created call {i + 1}/5 for user {user_id}")
                time.sleep(0.5)  # Задержка между созданием звонков

            except Exception as e:
                logger.error(f"Error creating call {i + 1}: {str(e)}")
                continue

    return redirect("telephony")
















