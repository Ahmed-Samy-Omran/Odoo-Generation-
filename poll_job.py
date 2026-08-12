import requests, time, sys
from api_client import auth_headers

JOB='2442203d-6b07-439e-9706-def3dcb6f68e'
BASE='http://127.0.0.1:8000'
headers=auth_headers(BASE)
url=f'{BASE}/job/{JOB}'
for _ in range(60):
    r=requests.get(url, headers=headers, timeout=10)
    data=r.json()
    print(data['status'], data['progress'], data.get('message'))
    if data['status'] in ('done','error'):
        print('final', data)
        break
    time.sleep(1)
else:
    print('timeout')
    sys.exit(1)
# attempt download if done
if data['status']=='done' and data.get('download_url'):
    dl=BASE+data['download_url']
    r=requests.get(dl, headers=headers, timeout=20)
    open('result.zip','wb').write(r.content)
    print('downloaded result.zip')
