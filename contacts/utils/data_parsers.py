def client_parser(batch):
    data = []

    for key, entry in batch.items():
        if key.startswith('contact_'):
            contact = entry['result']

            contact_id = contact['ID']
            company_id = contact.get('COMPANY_ID')
            company = (batch.get(f'company_{company_id}') or {}).get('result', {})

            name = contact.get('NAME')
            second_name = contact.get('SECOND_NAME') or ''
            last_name = contact.get('LAST_NAME') or ''
            phone_number = contact.get('PHONE', [{}])[0].get('VALUE') or ''
            email_address = contact.get('EMAIL', [{}])[0].get('VALUE') or ''
            company_title = company.get('TITLE') or ''

            data.append({
                'contact_ID': contact_id,
                'contact_NAME': name,
                'contact_SECOND_NAME': second_name,
                'contact_LAST_NAME': last_name,
                'contact_PHONE': phone_number,
                'contact_EMAIL': email_address,
                'company_TITLE': company_title,
            })

    return data