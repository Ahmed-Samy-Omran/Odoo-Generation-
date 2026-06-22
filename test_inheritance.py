import os
import json
from app.generators.OdooModuleGenerator import OdooModuleGenerator


def test_generation():
    # Define a test configuration with inheritance and multiple modules
    config = {
        "module_name": "test_inheritance_module",
        "module_description": "A module to test inheritance logic",
        "depends": ["base", "sale"],
        "models": [
            {
                "name": "res.partner",
                "description": "Customized Partner",
                "is_inherit": True,
                "inherit_model": "res.partner",
                "is_customization": True,
                "fields": [
                    {"name": "x_custom_field", "type": "char", "label": "Custom Field"}
                ]
            },
            {
                "name": "test.new.model",
                "description": "New Model",
                "is_inherit": True,
                "inherit_model": "res.partner",
                "is_customization": False,
                "fields": [
                    {"name": "name", "type": "char", "label": "Name"}
                ]
            }
        ],
        "actions": [
            {
                "name": "New Model Action",
                "res_model": "test.new.model",
                "view_mode": "tree,form"
            }
        ],
        "menus": [
            {
                "name": "Test Root",
                "sequence": 10
            },
            {
                "name": "New Model Menu",
                "parent_xml_id": "test_root_menu",
                "action_xml_id": "new_model_action_action",
                "sequence": 10
            }
        ]
    }

    templates_dir = "templates"
    output_dir = "generated_modules_test"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    generator = OdooModuleGenerator(templates_dir)
    module_path = generator.generate_module(config, output_dir)

    print(f"Module generated at: {module_path}")

    # Check if files exist and have expected content
    model_file = os.path.join(module_path, "models", "res_partner.py")
    if os.path.exists(model_file):
        with open(model_file, 'r') as f:
            content = f.read()
            print("\n--- res_partner.py content ---")
            print(content)
            if "_inherit = 'res.partner'" in content and "_name =" not in content:
                print("SUCCESS: res_partner.py correctly uses _inherit without _name for customization.")
            else:
                print("FAILURE: res_partner.py logic is incorrect.")

    new_model_file = os.path.join(module_path, "models", "test_new_model.py")
    if os.path.exists(new_model_file):
        with open(new_model_file, 'r') as f:
            content = f.read()
            print("\n--- test_new_model.py content ---")
            print(content)
            if "_inherit = 'res.partner'" in content and "_name = 'test.new.model'" in content:
                print("SUCCESS: test_new_model.py correctly uses both _inherit and _name.")
            else:
                print("FAILURE: test_new_model.py logic is incorrect.")

    view_file = os.path.join(module_path, "views", "res_partner_views.xml")
    if os.path.exists(view_file):
        with open(view_file, 'r') as f:
            content = f.read()
            print("\n--- res_partner_views.xml content ---")
            print(content)
            if "inherit_id" in content and "xpath" in content:
                print("SUCCESS: res_partner_views.xml correctly uses xpath for customization.")
            else:
                print("FAILURE: res_partner_views.xml logic is incorrect.")

    manifest_file = os.path.join(module_path, "__manifest__.py")
    if os.path.exists(manifest_file):
        with open(manifest_file, 'r') as f:
            content = f.read()
            print("\n--- __manifest__.py content ---")
            print(content)
            if "'security/ir.model.access.csv'" in content:
                print("SUCCESS: Manifest correctly includes security for new models.")
            else:
                print("FAILURE: Manifest missing security.")


if __name__ == "__main__":
    test_generation()
