import requests, json
url='http://127.0.0.1:8000/generate-module/'
payload={
  "modules":[
    {
      "module_name":"demo_lib",
      "module_description":"Demo library module",
      "models":[
        {"name":"book","description":"Book","rec_name":"name","fields":[{"name":"name","type":"char","label":"Title","required":True},{"name":"isbn","type":"char","label":"ISBN"}],"tree_view_fields":["name","isbn"],"form_view_fields":["name","isbn"]}
      ],
      "actions":[{"name":"Books","res_model":"book","view_mode":"tree,form"}],
      "menus":[{"name":"Demo Library","sequence":10}]
    }
  ]
}

r=requests.post(url, json=payload, timeout=10)
print('status', r.status_code)
try:
    print(r.json())
except Exception as e:
    print(r.text)
