import requests, time, json
from api_client import auth_headers

BASE = "http://127.0.0.1:8000"
headers = auth_headers(BASE)

payload = {
    "modules": [
        {
            "module_name": "demo_lib",
            "module_description": "Demo library module",
            "models": [
                {
                    "name": "book",
                    "description": "Book",
                    "rec_name": "name",
                    "fields": [
                        {"name": "name", "type": "char", "label": "Title", "required": True},
                        {"name": "isbn", "type": "char", "label": "ISBN"},
                    ],
                    "tree_view_fields": ["name", "isbn"],
                    "form_view_fields": ["name", "isbn"],
                }
            ],
            "actions": [{"name": "Books", "res_model": "book", "view_mode": "tree,form"}],
            "menus": [{"name": "Demo Library", "sequence": 10}],
        }
    ]
}

resp = requests.post(f"{BASE}/generate-module/", json=payload, headers=headers, timeout=10)
print("submit_status", resp.status_code)
print(resp.text)
job_id = resp.json().get("job_id")
for i in range(30):
    time.sleep(2)
    r = requests.get(f"{BASE}/job/{job_id}", headers=headers, timeout=10)
    data = r.json()
    print("attempt", i + 1, "status", data.get("status"), "progress", data.get("progress"), "message", data.get("message"), "error", data.get("error"))
    if data.get("status") in {"done", "error"}:
        break
