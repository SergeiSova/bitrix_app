from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth


def prepare_userdata(user, calls):
    user_id = user['ID']
    username = user['NAME'] + ' ' + user['LAST_NAME']
    calls_num = len([call for call in calls if call['PORTAL_USER_ID'] == user_id])

    return {'id': user_id, 'name': username, 'work_position': user['WORK_POSITION'], 'avatar': user.get('PERSONAL_PHOTO'), 'calls24': calls_num}


def get_supervisors(departments, department_id):
    def step(current_id, supervisors):
        node = departments.get(str(current_id))

        if node is None or current_id is None:
            return supervisors

        supervisor = node.get('UF_HEAD')

        if supervisor:
            supervisors.append(supervisor)

        parent = node.get('PARENT')

        return step(parent, supervisors)

    return step(department_id, [])

@main_auth(on_cookies=True)
def employees_telephony(request):

    but = request.bitrix_user_token
    departments = but.call_list_method('department.get', {
        'sort': 'ID',
        'order': 'ASC',
    })
    departments = {department.get('ID'): department for department in departments}

    users = but.call_list_method('user.get', {'FILTER': {'!UF_DEPARTMENT': []}})
    users = {user.get('ID'): user for user in users}

    calls = but.call_list_method('voximplant.statistic.get', {
                'FILTER': {
                    'CALL_TYPE': '1',
                    '>CALL_DURATION': 60,
                    '>CALL_START_DATE': (timezone.now()  - timedelta(hours=24)).isoformat()
                }
            })

    department_users = {}
    for user in users.values():
        for department_id in user['UF_DEPARTMENT']:
            department_users[department_id] = department_users.get(department_id, []) + [user]

    context = []
    for department_id, department_employees in department_users.items():
        department_name = departments[str(department_id)]['NAME']
        employees_list = [prepare_userdata(user, calls) for user in department_employees]
        supervisors = [user for user in users.values() if user['ID'] in get_supervisors(departments, department_id)]
        supervisors_names = [user['NAME'] for user in supervisors]

        context.append({
            'departament_ID': department_id,
            'departament_NAME': department_name,
            'managers_list': supervisors_names,
            'employees_list': employees_list,
        })

    return render(request, 'staff_table.html', {"context": context})