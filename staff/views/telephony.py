import logging
import os
import random
import time

from django.shortcuts import redirect
from django.utils import timezone

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth

logger = logging.getLogger(__name__)


def generate_phone_number():
    return '+79' + ''.join([str(random.randint(0, 9)) for _ in range(9)])


@main_auth(on_cookies=True)
def call_generator(request):
    """Создать тестовые звонки. Работает только при ENABLE_TEST_CALL_GENERATOR=1."""
    if request.method == 'POST' and os.getenv('ENABLE_TEST_CALL_GENERATOR') == '1':
        but = request.bitrix_user_token
        user_result = but.call_list_method('user.get', {'FILTER': {'ACTIVE': 'Y'}})
        user_ids = [user['ID'] for user in user_result]
        now = timezone.now()

        for i in range(5 if user_ids else 0):
            try:
                user_id = int(random.choice(user_ids))
                duration = random.randint(61, 120)

                call = but.call_api_method('telephony.externalcall.register', {
                    'USER_ID': user_id,
                    'PHONE_NUMBER': generate_phone_number(),
                    'CALL_START_DATE': now.isoformat(),
                    'TYPE': 1,
                    'CRM_CREATE': 0,
                    'SHOW': 0,
                })
                call_id = (call.get('result') or {}).get('CALL_ID')
                if not call_id:
                    logger.error('Call %s/5 was not registered', i + 1)
                    continue

                time.sleep(0.5)
                but.call_api_method('telephony.externalcall.finish', {
                    'CALL_ID': call_id,
                    'USER_ID': user_id,
                    'DURATION': duration,
                    'STATUS_CODE': '200',
                })
                logger.info('Successfully created call %s/5 for user %s', i + 1, user_id)
                time.sleep(0.5)
            except Exception as e:
                logger.error('Error creating call %s: %s', i + 1, type(e).__name__)

    return redirect('telephony')
