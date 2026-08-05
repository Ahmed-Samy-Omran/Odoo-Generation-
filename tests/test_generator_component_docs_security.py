import os
from pathlib import Path
from tempfile import TemporaryDirectory

from app.generators.OdooModuleGenerator import OdooModuleGenerator


def test_generate_docs_and_component_security_merges_files(tmp_path):
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    generator = OdooModuleGenerator(templates_dir=templates_dir)

    # Create a fake component registry directory structure inside tmp_path
    registry_root = tmp_path / "knowledge_registry"
    component_dir = registry_root / "hospital_management" / "v1.0"
    component_dir.mkdir(parents=True, exist_ok=True)
    (component_dir / "business_rules.md").write_text("Business rules for hospital module", encoding="utf-8")
    adrs_dir = component_dir / "adrs"
    adrs_dir.mkdir(parents=True, exist_ok=True)
    (adrs_dir / "001-initial-design.md").write_text("Initial design decisions", encoding="utf-8")
    security_dir = component_dir / "security"
    security_dir.mkdir(parents=True, exist_ok=True)
    (security_dir / "ir.model.access.csv").write_text(
        "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"
        "hospital_patient_hospital_access,hospital.patient,model_hospital_patient,base.group_user,1,0,0,0\n",
        encoding="utf-8"
    )

    # Prepare a minimal config with matched component id
    config = {
        "module_name": "hospital_management",
        "module_description": "Hospital management module",
        "depends": ["base"],
        "models": [],
        "matched_components": ["hospital_management/v1.0"],
    }

    # Monkey patch the ComponentRegistryService path resolution by temporarily setting env var
    os.environ["KNOWLEDGE_REGISTRY_PATH"] = str(registry_root)

    try:
        output_dir = tmp_path / "output"
        module_path = generator.generate_module(config, str(output_dir))

        docs_dir = Path(module_path) / "docs"
        security_csv = Path(module_path) / "security" / "ir.model.access.csv"

        assert docs_dir.exists()
        assert (docs_dir / "business_rules.md").exists()
        assert (docs_dir / "001-initial-design.md").exists()
        assert security_csv.exists()

        content = security_csv.read_text(encoding="utf-8")
        assert "hospital_patient_hospital_access" in content
        assert "base.group_user" in content
    finally:
        del os.environ["KNOWLEDGE_REGISTRY_PATH"]
