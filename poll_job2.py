import requests, time, sys
JOB='2442203d-6b07-439e-9706-def3dcb6f68e'
url=f'http://127.0.0.1:8000/job/{JOB}'
for _ in range(60):
    r=requests.get(url, timeout=10)
    print('code', r.status_code)
    print('text', r.text[:1000])
    try:
        data=r.json()
    except Exception as e:
        print('json-error', e)
        break
    print(data.get('status'), data.get('progress'), data.get('message'))
    if data.get('status') in ('done','error'):
        print('final', data)
        break
    time.sleep(1)
else:
    print('timeout')
    sys.exit(1)
if data.get('status')=='done' and data.get('download_url'):
    dl='http://127.0.0.1:8000'+data['download_url']
    r=requests.get(dl, timeout=20)
    open('result.zip','wb').write(r.content)
    print('downloaded result.zip')
