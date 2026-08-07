import csv
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.component_registry_service import ComponentRegistryService
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class OdooModuleGenerator:
    """Generate Odoo modules from JSON configuration."""

    def __init__(self, templates_dir: str):
        """Initialize the generator with templates directory.

        Args:
            templates_dir: Path to Jinja2 templates directory.
        """
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.output_dir: Optional[Path] = None

    def generate_module(self, config: Dict[str, Any], output_dir: str) -> str:
        """Generate complete Odoo module from JSON configuration.

        Args:
            config: Dictionary containing module configuration.
            output_dir: Directory to generate module in.

        Returns:
            Path to generated module directory.
        """
        self.output_dir = Path(output_dir)
        config = self._preprocess_config(config)

        module_name = config.get("module_name", "custom_module")
        module_path = self.output_dir / module_name
        module_path.mkdir(parents=True, exist_ok=True)

        self._create_directory_structure(module_path)
        self._generate_docs(config, module_path)

        self._generate_manifest(config, module_path)
        self._generate_security_groups(config, module_path)
        self._generate_models(config, module_path)
        self._generate_views(config, module_path)
        self._generate_security(config, module_path)
        self._generate_component_security(config, module_path)
        self._generate_actions(config, module_path)
        self._generate_menus(config, module_path)
        self._generate_reports(config, module_path)
        self._generate_init_files(config, module_path)

        return str(module_path)

    def _preprocess_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess the config to normalize fields and resolve menu/action references."""
        module_name = config.get("module_name", "custom_module")

        self._normalize_fields(config)
        menu_id_map = self._build_xml_id_map(config.get("menus") or [], suffix="menu")
        action_id_map = self._build_xml_id_map(config.get("actions") or [], suffix="action")
        self._resolve_menu_references(config, module_name, menu_id_map, action_id_map)
        logger.debug("Preprocessed config for module %s", module_name)

        return config

    def _normalize_fields(self, config: Dict[str, Any]) -> None:
        """Normalize field definitions and ensure view field lists exist."""
        for model in config.get("models", []):
            fields = model.get("fields", [])
            field_names: List[str] = []
            for field in fields:
                if "type" in field and isinstance(field["type"], str):
                    field["type"] = field["type"].lower()

                if field.get("type") == "selection" and not field.get("selection_options"):
                    field["type"] = "char"
                    field["label"] = (
                        f"[WARNING] Selection field {field.get('name')} converted to Char. "
                        "No selection_options provided."
                    )

                if field.get("name"):
                    field_names.append(field["name"])

            model.setdefault("tree_view_fields", field_names[:5])
            model.setdefault("form_view_fields", field_names)

    @staticmethod
    def _clean_name(value: str) -> str:
        """Normalize a name string to a safe XML ID component."""
        return value.lower().replace(".", "_").replace(" ", "_")

    def _build_xml_id_map(self, items: List[Dict[str, Any]], suffix: str) -> Dict[str, str]:
        """Build a mapping from name variants to generated XML IDs."""
        id_map: Dict[str, str] = {}
        for item in items:
            name = item.get("name", "")
            if not name:
                continue
            snake_name = self._clean_name(name)
            base_id = f"{snake_name}_{suffix}"
            aliases = [
                base_id,
                snake_name,
                f"{suffix}_{snake_name}",
                f"{suffix}_{snake_name}_{suffix}",
            ]
            for alias in aliases:
                id_map[alias] = base_id
        return id_map

    def _resolve_menu_references(
        self,
        config: Dict[str, Any],
        module_name: str,
        menu_id_map: Dict[str, str],
        action_id_map: Dict[str, str],
    ) -> None:
        """Resolve menu parent and action references to normalized XML IDs."""

        def resolve_reference(ref_value: str, id_map: Dict[str, str]) -> Optional[str]:
            ref_id = ref_value.split(".")[-1]
            if ref_id in id_map:
                return id_map[ref_id]
            if len(ref_value.split(".")) > 1:
                prefix = ref_value.split(".")[0]
                if prefix == module_name or prefix in ["hospital_management", "gym_management", "custom_module"]:
                    return id_map.get(ref_id)
            guessed_id = self._clean_name(ref_value)
            if id_map is action_id_map:
                return id_map.get(f"{guessed_id}_action")
            return id_map.get(guessed_id)

        for menu in config.get("menus") or []:
            parent = menu.get("parent_xml_id")
            if parent:
                resolved_parent = resolve_reference(parent, menu_id_map)
                if resolved_parent:
                    menu["parent_xml_id"] = resolved_parent

            action_ref = menu.get("action_xml_id")
            if action_ref:
                resolved_action = resolve_reference(action_ref, action_id_map)
                if resolved_action:
                    menu["action_xml_id"] = resolved_action

    def _create_directory_structure(self, module_path: str) -> None:
        """Create the basic Odoo module directory structure"""
        directories = [
            module_path,
            os.path.join(module_path, "models"),
            os.path.join(module_path, "views"),
            os.path.join(module_path, "security"),
            os.path.join(module_path, "reports"),  # New: for QWeb reports
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _generate_manifest(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate __manifest__.py file"""
        template = self.env.get_template("manifest_template.j2")

        data_files = []
        # Only add security for non-customization modules or new models
        has_new_models = any(not model.get("is_customization") for model in config.get("models", []))
        if has_new_models:
            data_files.append("security/ir.model.access.csv")

        # New: Add security groups to manifest
        if config.get("security_groups"):
            data_files.append("security/security.xml")

        for model in config.get("models", []):
            model_name_snake = model.get("name", "model").replace(".", "_")
            data_files.append(f"views/{model_name_snake}_views.xml")

        # Add actions and menus to data files
        if config.get("actions"):
            data_files.append("views/actions.xml")
        if config.get("menus"):
            data_files.append("views/menus.xml")

        # New: Add report XML files to manifest
        for model in config.get("models", []):
            if model.get("print_reports"):
                for report in model["print_reports"]:
                    report_name_snake = report["report_name"].replace(".", "_")
                    data_files.append(f"reports/{report_name_snake}_report.xml")
                    data_files.append(f"reports/{report_name_snake}_template.xml")

        content = template.render(
            module_name=config.get("module_name", "custom_module"),
            module_description=config.get("module_description", ""),
            depends=config.get("depends", ["base"]),
            odoo_version=config.get("odoo_version") or config.get("version") or "17.0",
            data_files=data_files
        )

        manifest_path = os.path.join(module_path, "__manifest__.py")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_models(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate model files"""
        template = self.env.get_template("model_template.j2")
        models_dir = os.path.join(module_path, "models")

        for model in config.get("models", []):
            # Convert model name to class name (e.g., 'hospital.patient' -> 'HospitalPatient')
            name_to_use = model.get("inherit_model") if model.get("is_inherit") and model.get(
                "inherit_model") else model.get("name", "")
            class_name = "".join(word.capitalize() for word in name_to_use.replace(".", "_").split("_"))

            content = template.render(
                class_name=class_name,
                model_name=model.get("name"),
                model_description=model.get("description", ""),
                rec_name=model.get("rec_name", None),
                fields=model.get("fields", []),
                is_inherit=model.get("is_inherit", False),
                inherit_model=model.get("inherit_model"),
                is_customization=model.get("is_customization", False)
            )

            model_file_name = model.get("name", "model").replace(".", "_")
            model_file = os.path.join(models_dir, f"{model_file_name}.py")
            with open(model_file, "w", encoding="utf-8") as f:
                f.write(content)

    def _generate_views(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate view XML files (form, tree, search, kanban, calendar, dashboard)"""
        views_dir = os.path.join(module_path, "views")
        Path(views_dir).mkdir(parents=True, exist_ok=True)

        for model in config.get("models", []):
            model_name = model.get("name", "model")
            model_label = model.get("description", model.get("name", "Model").replace(".", " ").title())
            model_name_snake = model.get("name", "model").replace(".", "_")

            # Generate combined view XML for form, tree, and search
            view_template = self.env.get_template("view_template.j2")
            content = view_template.render(
                module_name=config.get("module_name"),  # Pass module name for XML IDs
                model_name=model_name,
                model_label=model_label,
                fields=model.get("fields", []),
                tree_view_fields=model.get("tree_view_fields", []),
                form_view_fields=model.get("form_view_fields", []),
                search_view=model.get("search_view", {}),
                is_inherit=model.get("is_inherit", False),
                inherit_model=model.get("inherit_model"),
                is_customization=model.get("is_customization", False),
                kanban_view=model.get("kanban_view"),
                calendar_view=model.get("calendar_view"),
                dashboard_view=model.get("dashboard_view")
            )

            view_file = os.path.join(views_dir, f"{model_name_snake}_views.xml")
            with open(view_file, "w", encoding="utf-8") as f:
                f.write(content)

    def _generate_security(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate security CSV file"""
        # Filter out models that are customizations of existing models (they already have security)
        models_to_secure = [
            model for model in config.get("models", [])
            if not model.get("is_customization")
        ]

        if not models_to_secure:
            return

        template = self.env.get_template("security_template.j2")
        content = template.render(
            module_name=config.get("module_name"),
            models=[
                {
                    "name": model.get("name", "model"),
                    "label": model.get("description", model.get("name", "Model").replace(".", " ").title())
                }
                for model in models_to_secure
            ]
        )

        security_file = os.path.join(module_path, "security", "ir.model.access.csv")
        with open(security_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_security_groups(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate security group XML file"""
        security_groups = config.get("security_groups", [])
        if not security_groups:
            return

        security_dir = os.path.join(module_path, "security")
        Path(security_dir).mkdir(parents=True, exist_ok=True)

        template = self.env.get_template("security_groups_template.j2")
        content = template.render(
            module_name=config.get("module_name"),
            security_groups=security_groups
        )

        security_file = os.path.join(security_dir, "security.xml")
        with open(security_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_docs(self, config: Dict[str, Any], module_path: str) -> None:
        """Copy ADRs and business rules from matched components into module docs/ folder."""
        matched = config.get("matched_components") or []
        if not matched:
            return

        docs_dir = os.path.join(module_path, "docs")
        Path(docs_dir).mkdir(parents=True, exist_ok=True)

        registry = ComponentRegistryService()
        for comp_id in matched:
            comp_dir = registry.get_component_dir(comp_id)
            if not comp_dir:
                continue

            # Copy business_rules.md if present
            br = Path(comp_dir) / "business_rules.md"
            if br.exists() and br.is_file():
                shutil.copy(str(br), os.path.join(docs_dir, br.name))

            # Copy adrs/ folder markdown files
            adrs_dir = Path(comp_dir) / "adrs"
            if adrs_dir.exists() and adrs_dir.is_dir():
                for f in sorted(adrs_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() == ".md":
                        shutil.copy(str(f), os.path.join(docs_dir, f.name))

            # Copy docs/ folder markdown files
            docs_source_dir = Path(comp_dir) / "docs"
            if docs_source_dir.exists() and docs_source_dir.is_dir():
                for f in sorted(docs_source_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() == ".md":
                        shutil.copy(str(f), os.path.join(docs_dir, f.name))

            # Also copy any ADR-like md files at component root (e.g., 001-*.md or *adr*.md)
            for f in sorted(Path(comp_dir).iterdir()):
                if f.is_file() and f.suffix.lower() == ".md":
                    name = f.name.lower()
                    if name.startswith("00") or "adr" in name:
                        shutil.copy(str(f), os.path.join(docs_dir, f.name))

    def _generate_component_security(self, config: Dict[str, Any], module_path: str) -> None:
        """Merge security rule lines from matched components into module's ir.model.access.csv."""
        matched = config.get("matched_components") or []
        if not matched:
            return

        registry = ComponentRegistryService()
        security_dir = Path(module_path) / "security"
        security_dir.mkdir(parents=True, exist_ok=True)
        module_security = security_dir / "ir.model.access.csv"

        # Read existing entries (skip header)
        existing_lines: List[str] = []
        header = "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink"
        if module_security.exists():
            lines = module_security.read_text(encoding="utf-8").splitlines()
            if lines:
                # assume first line is header if it contains id,name
                if "id," in lines[0].lower():
                    header = lines[0]
                    existing_lines = lines[1:]
                else:
                    existing_lines = lines

        to_add: List[str] = []
        for comp_id in matched:
            comp_dir = registry.get_component_dir(comp_id)
            if not comp_dir:
                continue

            candidates = [
                Path(comp_dir) / "security" / "ir.model.access.csv",
                Path(comp_dir) / "security" / "rules.csv",
                Path(comp_dir) / "security_rules.csv",
                Path(comp_dir) / "ir.model.access.csv",
            ]
            for cand in candidates:
                if cand.exists() and cand.is_file():
                    lines = cand.read_text(encoding="utf-8").splitlines()
                    for ln in lines:
                        ln_strip = ln.strip()
                        if not ln_strip:
                            continue
                        low = ln_strip.lower()
                        # skip header-like lines
                        if low.startswith("id,") or "model_id" in low:
                            continue
                        if ln_strip not in existing_lines and ln_strip not in to_add:
                            to_add.append(ln_strip)

        if to_add:
            with open(module_security, "w", encoding="utf-8") as f:
                f.write(header + "\n")
                for ln in existing_lines:
                    f.write(ln + "\n")
                for ln in to_add:
                    f.write(ln + "\n")

    def _generate_actions(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate action XML files"""
        actions = config.get("actions") or []
        if not actions:
            return

        views_dir = os.path.join(module_path, "views")
        Path(views_dir).mkdir(parents=True, exist_ok=True)

        action_template = self.env.get_template("action_template.j2")
        content = action_template.render(actions=actions)

        actions_file = os.path.join(views_dir, "actions.xml")
        with open(actions_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_menus(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate menu XML files"""
        menus = config.get("menus") or []
        if not menus:
            return

        views_dir = os.path.join(module_path, "views")
        Path(views_dir).mkdir(parents=True, exist_ok=True)

        menu_template = self.env.get_template("menu_template.j2")
        content = menu_template.render(menus=menus)

        menus_file = os.path.join(views_dir, "menus.xml")
        with open(menus_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_reports(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate QWeb report XML files and templates"""
        reports_dir = os.path.join(module_path, "reports")
        Path(reports_dir).mkdir(parents=True, exist_ok=True)

        report_xml_template = self.env.get_template("report_xml_template.j2")
        report_qweb_template = self.env.get_template("report_qweb_template.j2")

        for model in config.get("models", []):
            if model.get("print_reports"):
                for report in model["print_reports"]:
                    report_name_snake = report["report_name"].replace(".", "_")

                    # 1. Generate report XML definition (The Link between Report and Model)
                    report_xml_content = report_xml_template.render(
                        module_name=config.get("module_name"),
                        report_name=report["report_name"],
                        report_label=report["report_label"],
                        report_type=report["report_type"],
                        model_name=model["name"],
                        report_name_snake=report_name_snake
                    )
                    report_xml_file = os.path.join(reports_dir, f"{report_name_snake}_report.xml")
                    with open(report_xml_file, "w", encoding="utf-8") as f:
                        f.write(report_xml_content)

                    # 2. Generate QWeb report template (The Actual HTML/PDF Design)
                    report_qweb_content = report_qweb_template.render(
                        module_name=config.get("module_name"),
                        report_name=report["report_name"],
                        report_label=report["report_label"],
                        model_name=model["name"],
                        fields=model.get("fields", [])
                    )
                    report_qweb_file = os.path.join(reports_dir, f"{report_name_snake}_template.xml")
                    with open(report_qweb_file, "w", encoding="utf-8") as f:
                        f.write(report_qweb_content)

    def _generate_init_files(self, config: Dict[str, Any], module_path: str) -> None:
        """Generate __init__.py files for module and models package."""
        init_template = self.env.get_template("init_template.j2")
        models_init_template = self.env.get_template("models_init_template.j2")

        module_init = init_template.render()
        with open(os.path.join(module_path, "__init__.py"), "w", encoding="utf-8") as f:
            f.write(module_init)

        model_files = [
            model.get("name", "model").replace(".", "_")
            for model in config.get("models", [])
        ]
        models_init = models_init_template.render(model_files=model_files)
        with open(os.path.join(module_path, "models", "__init__.py"), "w", encoding="utf-8") as f:
            f.write(models_init)