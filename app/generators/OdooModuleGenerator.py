import os
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, List, Any, Optional


class OdooModuleGenerator:
    """Generate Odoo modules from JSON configuration"""

    def __init__(self, templates_dir: str):
        """
        Initialize the generator with templates directory

        Args:
            templates_dir: Path to Jinja2 templates directory
        """
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.output_dir = None

    def generate_module(self, config: Dict[str, Any], output_dir: str) -> str:
        """
        Generate complete Odoo module from JSON configuration

        Args:
            config: Dictionary containing module configuration
            output_dir: Directory to generate module in

        Returns:
            Path to generated module directory
        """
        self.output_dir = output_dir
        
        # Preprocess and clean config
        config = self._preprocess_config(config)
        
        module_name = config.get('module_name', 'custom_module')
        module_path = os.path.join(output_dir, module_name)

        # Create module directory structure
        self._create_directory_structure(module_path)

        # Generate all files
        self._generate_manifest(config, module_path)
        self._generate_models(config, module_path)
        self._generate_views(config, module_path)
        self._generate_security(config, module_path)
        self._generate_actions(config, module_path)
        self._generate_menus(config, module_path)
        self._generate_init_files(config, module_path)

        return module_path

    def _preprocess_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess and clean up the config to ensure correct casing and reference resolving"""
        module_name = config.get('module_name', 'custom_module')

        # 1. Normalize field types to lowercase and populate missing view fields
        for model in config.get('models', []):
            fields = model.get('fields', [])
            field_names = []
            for field in fields:
                if 'type' in field:
                    field['type'] = field['type'].lower()
                if field.get('name'):
                    field_names.append(field['name'])

            if not model.get('tree_view_fields'):
                model['tree_view_fields'] = field_names[:5]
            if not model.get('form_view_fields'):
                model['form_view_fields'] = field_names

        # 2. Build XML ID maps for local menus and actions
        def clean_name(name: str) -> str:
            return name.lower().replace('.', '_').replace(' ', '_')

        menu_id_map = {}
        for menu in config.get('menus', []):
            name = menu.get('name', '')
            if not name:
                continue
            gen_id = f"{clean_name(name)}_menu"
            snake_name = clean_name(name)
            
            # Map various ways AI might refer to this menu to the actual ID
            for ref in [gen_id, snake_name, f"menu_{snake_name}", f"menu_{snake_name}_menu", f"menu_{snake_name}_root"]:
                menu_id_map[ref] = gen_id

        action_id_map = {}
        for action in config.get('actions', []):
            name = action.get('name', '')
            if not name:
                continue
            gen_id = f"{clean_name(name)}_action"
            snake_name = clean_name(name)
            
            for ref in [gen_id, snake_name, f"action_{snake_name}", f"action_{snake_name}_action"]:
                action_id_map[ref] = gen_id

        # 3. Resolve parent_xml_id and action_xml_id references
        for menu in config.get('menus', []):
            # Resolve parent_xml_id
            parent = menu.get('parent_xml_id')
            if parent:
                parts = parent.split('.')
                ref_id = parts[-1]
                if ref_id in menu_id_map:
                    menu['parent_xml_id'] = menu_id_map[ref_id]
                elif len(parts) > 1:
                    prefix = parts[0]
                    if prefix == module_name or prefix in ['hospital_management', 'gym_management', 'custom_module']:
                        if ref_id in menu_id_map:
                            menu['parent_xml_id'] = menu_id_map[ref_id]
                        else:
                            # Default to the first root menu if prefix matches but ID is not found
                            root_menus = [m for m in config.get('menus', []) if not m.get('parent_xml_id')]
                            if root_menus:
                                menu['parent_xml_id'] = f"{clean_name(root_menus[0]['name'])}_menu"

            # Resolve action_xml_id
            action_ref = menu.get('action_xml_id')
            if action_ref:
                parts = action_ref.split('.')
                ref_id = parts[-1]
                if ref_id in action_id_map:
                    menu['action_xml_id'] = action_id_map[ref_id]
                elif len(parts) > 1:
                    prefix = parts[0]
                    if prefix == module_name or prefix in ['hospital_management', 'gym_management', 'custom_module']:
                        if ref_id in action_id_map:
                            menu['action_xml_id'] = action_id_map[ref_id]
                else:
                    menu_snake = clean_name(menu.get('name', ''))
                    guessed_id = f"{menu_snake}_action"
                    if guessed_id in action_id_map:
                        menu['action_xml_id'] = guessed_id

        return config

    def _create_directory_structure(self, module_path: str) -> None:
        """Create the basic Odoo module directory structure"""
        directories = [
            module_path,
            os.path.join(module_path, 'models'),
            os.path.join(module_path, 'views'),
            os.path.join(module_path, 'security'),
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _generate_manifest(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate __manifest__.py file"""
        template = self.env.get_template('manifest_template.j2')

        data_files = ['security/ir.model.access.csv']
        for model in config.get('models', []):
            model_name_snake = model.get('name', 'model').replace('.', '_')
            data_files.append(f'views/{model_name_snake}_views.xml')

        # Add actions and menus to data files
        if config.get('actions'):
            data_files.append('views/actions.xml')
        if config.get('menus'):
            data_files.append('views/menus.xml')

        content = template.render(
            module_name=config.get('module_name', 'custom_module'),
            module_description=config.get('module_description', ''),
            depends=config.get('depends', ['base']),
            data_files=data_files
        )

        manifest_path = os.path.join(module_path, '__manifest__.py')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_models(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate model files"""
        template = self.env.get_template('model_template.j2')
        models_dir = os.path.join(module_path, 'models')

        for model in config.get('models', []):
            # Convert model name to class name (e.g., 'hospital.patient' -> 'HospitalPatient')
            class_name = ''.join(word.capitalize() for word in model.get('name', '').replace('.', '_').split('_'))
            model_name = model.get('name', 'model')

            content = template.render(
                class_name=class_name,
                model_name=model_name,
                model_description=model.get('description', ''),
                rec_name=model.get('rec_name', None),
                fields=model.get('fields', [])
            )

            model_file_name = model.get('name', 'model').replace('.', '_')
            model_file = os.path.join(models_dir, f"{model_file_name}.py")
            with open(model_file, 'w', encoding='utf-8') as f:
                f.write(content)

    def _generate_views(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate view XML files (form, tree, search)"""
        views_dir = os.path.join(module_path, 'views')
        Path(views_dir).mkdir(parents=True, exist_ok=True)

        for model in config.get('models', []):
            model_name = model.get('name', 'model')
            model_label = model.get('description', model.get('name', 'Model').replace('.', ' ').title())
            model_name_snake = model.get('name', 'model').replace('.', '_')

            # Generate combined view XML for form, tree, and search
            view_template = self.env.get_template('view_template.j2')
            content = view_template.render(
                model_name=model_name,
                model_label=model_label,
                fields=model.get('fields', []),
                tree_view_fields=model.get('tree_view_fields', []),
                form_view_fields=model.get('form_view_fields', []),
                search_view=model.get('search_view', {})
            )

            view_file = os.path.join(views_dir, f"{model_name_snake}_views.xml")
            with open(view_file, 'w', encoding='utf-8') as f:
                f.write(content)

    def _generate_security(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate security CSV file"""
        template = self.env.get_template('security_template.j2')
        content = template.render(
            models=[
                {
                    'name': model.get('name', 'model'),
                    'label': model.get('description', model.get('name', 'Model').replace('.', ' ').title())
                }
                for model in config.get('models', [])
            ]
        )

        security_file = os.path.join(module_path, 'security', 'ir.model.access.csv')
        with open(security_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_actions(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate action XML files"""
        actions = config.get('actions', [])
        if not actions:
            return

        views_dir = os.path.join(module_path, 'views')
        Path(views_dir).mkdir(parents=True, exist_ok=True)

        action_template = self.env.get_template('action_template.j2')
        content = action_template.render(actions=actions)

        actions_file = os.path.join(views_dir, 'actions.xml')
        with open(actions_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_menus(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate menu XML files"""
        menus = config.get('menus', [])
        if not menus:
            return

        views_dir = os.path.join(module_path, 'views')
        Path(views_dir).mkdir(parents=True, exist_ok=True)

        menu_template = self.env.get_template('menu_template.j2')
        content = menu_template.render(menus=menus)

        menus_file = os.path.join(views_dir, 'menus.xml')
        with open(menus_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_init_files(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate __init__.py files"""
        # Main __init__.py
        init_template = self.env.get_template('init_template.j2')
        init_content = init_template.render()

        init_file = os.path.join(module_path, '__init__.py')
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)

        # Models __init__.py
        models_init_template = self.env.get_template('models_init_template.j2')

        # Pass model file names to the template (e.g., 'hospital_patient')
        model_files = []
        for model in config.get('models', []):
            model_file_name = model.get('name', 'model').replace('.', '_')
            model_files.append(model_file_name)

        models_init_content = models_init_template.render(
            model_files=model_files
        )

        models_init_file = os.path.join(module_path, 'models', '__init__.py')
        with open(models_init_file, 'w', encoding='utf-8') as f:
            f.write(models_init_content)


def generate_from_json(json_file: str, output_dir: str, templates_dir: str) -> str:
    """
    Convenience function to generate module from JSON file

    Args:
        json_file: Path to JSON configuration file
        output_dir: Directory to generate module in
        templates_dir: Path to templates directory

    Returns:
        Path to generated module directory
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    generator = OdooModuleGenerator(templates_dir)
    return generator.generate_module(config, output_dir)
