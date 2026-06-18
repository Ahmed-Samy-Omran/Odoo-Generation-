# -*- coding: utf-8 -*-
"""
Odoo Module Generator
Converts JSON configuration to Odoo module files
"""

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
        module_name = config.get('module_name', 'custom_module')
        module_path = os.path.join(output_dir, module_name)

        # Create module directory structure
        self._create_directory_structure(module_path)

        # Generate all files
        self._generate_manifest(config, module_path)
        self._generate_models(config, module_path)
        self._generate_views(config, module_path)
        self._generate_security(config, module_path)
        self._generate_init_files(config, module_path)

        return module_path

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
        content = template.render(
            module_name=config.get('module_name', 'custom_module'),
            module_description=config.get('module_description', ''),
            models=config.get('models', [])
        )

        manifest_path = os.path.join(module_path, '__manifest__.py')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_models(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate model files"""
        template = self.env.get_template('model_template.j2')
        models_dir = os.path.join(module_path, 'models')

        for model in config.get('models', []):
            # Convert model name to class name (e.g., 'patient' -> 'Patient')
            class_name = ''.join(word.capitalize() for word in model.get('name', '').split('_'))
            model_name = f"{config.get('module_name', 'custom')}.{model.get('name', 'model')}"

            content = template.render(
                class_name=class_name,
                model_name=model_name,
                model_description=model.get('description', ''),
                rec_name=model.get('rec_name', None),
                fields=model.get('fields', [])
            )

            model_file = os.path.join(models_dir, f"{model.get('name', 'model')}.py")
            with open(model_file, 'w', encoding='utf-8') as f:
                f.write(content)

    def _generate_views(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate view XML files"""
        template = self.env.get_template('view_template.j2')
        views_dir = os.path.join(module_path, 'views')

        for model in config.get('models', []):
            model_name = f"{config.get('module_name', 'custom')}.{model.get('name', 'model')}"
            model_label = model.get('label', model.get('name', 'Model').replace('_', ' ').title())

            content = template.render(
                model_name=model_name,
                model_label=model_label,
                fields=model.get('fields', [])
            )

            view_file = os.path.join(views_dir, f"{model.get('name', 'model')}_views.xml")
            with open(view_file, 'w', encoding='utf-8') as f:
                f.write(content)

    def _generate_security(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate security CSV file"""
        template = self.env.get_template('security_template.j2')
        content = template.render(
            models=[
                {
                    'name': model.get('name', 'model'),
                    'label': model.get('label', model.get('name', 'Model').replace('_', ' ').title())
                }
                for model in config.get('models', [])
            ]
        )

        security_file = os.path.join(module_path, 'security', 'ir.model.access.csv')
        with open(security_file, 'w', encoding='utf-8') as f:
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
        models_init_content = models_init_template.render(
            models=config.get('models', [])
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
