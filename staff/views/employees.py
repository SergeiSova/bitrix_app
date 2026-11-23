import logging
import os
from collections import Counter
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth

logger = logging.getLogger('bitrix')


def full_name(user):
    return ' '.join(filter(None, [user.get('NAME'), user.get('LAST_NAME')]))


def get_calls_last_24h(but):
    """Исходящие звонки длиннее минуты за 24 часа. None, если статистика недоступна."""
    since = (timezone.now() - timedelta(hours=24)).isoformat()
    try:
        calls = but.call_list_method('voximplant.statistic.get', {
            'FILTER': {'CALL_TYPE': 1, '>CALL_DURATION': 60, '>=CALL_START_DATE': since},
        })
    except Exception as e:
        logger.error('Could not load call statistics: %s', type(e).__name__)
        return None
    return Counter(str(call.get('PORTAL_USER_ID')) for call in calls)


def prepare_userdata(user, calls_by_user):
    user_id = user['ID']
    calls_num = None if calls_by_user is None else calls_by_user.get(str(user_id), 0)
    return {
        'id': user_id,
        'name': full_name(user),
        'work_position': user.get('WORK_POSITION'),
        'avatar': user.get('PERSONAL_PHOTO'),
        'calls24': calls_num,
    }


def get_supervisors(departments, department_id):
    supervisors = []
    seen = set()
    current_id = department_id
    while current_id is not None and str(current_id) not in seen:
        seen.add(str(current_id))
        node = departments.get(str(current_id))
        if node is None:
            break
        if node.get('UF_HEAD'):
            supervisors.append(str(node['UF_HEAD']))
        current_id = node.get('PARENT')
    return supervisors


@main_auth(on_cookies=True)
def employees_telephony(request):
    but = request.bitrix_user_token

    departments = but.call_list_method('department.get', {
        'sort': 'ID',
        'order': 'ASC',
    })
    departments = {str(department.get('ID')): department for department in departments}

    users = but.call_list_method('user.get', {'FILTER': {'!UF_DEPARTMENT': [], 'ACTIVE': 'Y'}})
    users = {str(user.get('ID')): user for user in users}
    calls_by_user = get_calls_last_24h(but)

    department_users = {}
    for user in users.values():
        for department_id in user.get('UF_DEPARTMENT') or []:
            department_users.setdefault(department_id, []).append(user)

    context = []
    for department_id, department_employees in department_users.items():
        department = departments.get(str(department_id), {})
        supervisor_ids = set(get_supervisors(departments, department_id))
        supervisors_names = [full_name(user) for user_id, user in users.items()
                             if user_id in supervisor_ids and full_name(user)]

        context.append({
            'departament_ID': department_id,
            'departament_NAME': department.get('NAME', f'Отдел {department_id}'),
            'managers_list': supervisors_names,
            'employees_list': [prepare_userdata(user, calls_by_user) for user in department_employees],
        })

    return render(request, 'staff_table.html', {
        'context': context,
        'can_generate_calls': os.getenv('ENABLE_TEST_CALL_GENERATOR') == '1',
    })
