import time
import httpx
from api_client import get_token

BASE = 'http://127.0.0.1:8001'
url = f'{BASE}/analyze-requirements/'
payload = {
    'prompt': 'Create a hospital management module with appointment scheduling and patient records',
    'odoo_version': '17.0'
}

with httpx.Client(timeout=60, headers={'Authorization': f'Bearer {get_token(BASE)}'}) as client:
    r = client.post(url, json=payload)
    print('status', r.status_code)
    print('body', r.text)
    if r.status_code != 200:
        raise SystemExit(1)
    job_id = r.json().get('job_id')
    print('job_id', job_id)
    if not job_id:
        raise SystemExit(2)
    for attempt in range(15):
        time.sleep(2)
        r2 = client.get(f'{BASE}/job/{job_id}')
        print('poll', attempt, r2.status_code, r2.text)
        if r2.status_code != 200:
            raise SystemExit(3)
        if r2.json().get('status') in ('done', 'error'):
            break
