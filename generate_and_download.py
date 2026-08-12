import requests
import time
import os
from api_client import session

BASE = 'http://127.0.0.1:8002'
PROMPT = 'Create a hospital management module with appointment scheduling and patient records'
OD = '17.0'

s = session(BASE)

print('Submitting analyze-requirements request...')
r = s.post(f'{BASE}/analyze-requirements/', json={'prompt': PROMPT, 'odoo_version': OD})
r.raise_for_status()
resp = r.json()
job_id = resp.get('job_id')
print('Job created:', job_id)

for i in range(120):
    r = s.get(f'{BASE}/job/{job_id}')
    r.raise_for_status()
    j = r.json()
    status = j.get('status')
    progress = j.get('progress')
    print(f'[{i}] status={status} progress={progress}')
    if status in ('done', 'error'):
        print('Final job state:', j)
        break
    time.sleep(2)

if status != 'done':
    raise SystemExit('Job did not complete successfully')

download_url = j.get('download_url')
if not download_url:
    print('No download_url in job; trying _zip_path fallback')
    # Try to use internal API to fetch download endpoint
    raise SystemExit('No download URL available')

if not download_url.startswith('http'):
    download_url = f'{BASE}{download_url}'

out_path = os.path.join(os.getcwd(), 'hospital_management.zip')
print('Downloading from', download_url)
with s.get(download_url, stream=True) as r:
    r.raise_for_status()
    with open(out_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
print('Downloaded to', out_path)
