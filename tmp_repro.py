import os
import sys
sys.path.insert(0, os.getcwd())
from app.generators.OdooModuleGenerator import OdooModuleGenerator
from app.services.zip_handler import ZipHandler

out = os.path.join(os.getcwd(), 'generated_modules_test', 'repro')
os.makedirs(out, exist_ok=True)
config = {
    'module_name': 'repro_mod',
    'module_description': 'test',
    'depends': ['base'],
    'models': [{'name': 'product', 'fields': [{'name': 'name', 'type': 'char', 'required': True}]}],
    'actions': [],
    'menus': [],
    'security_groups': []
}

gen = OdooModuleGenerator(templates_dir=os.path.join(os.getcwd(), 'templates'))
path = gen.generate_module(config, out)
print('generated', path)
zip_path = os.path.join(out, 'repro_mod.zip')
ZipHandler.create_batch_zip([path], zip_path)
print('zip ok', os.path.exists(zip_path), os.path.getsize(zip_path))
