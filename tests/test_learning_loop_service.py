import json
import os
from pathlib import Path

from app.services.learning_loop_service import append_learning_entry


def test_append_learning_entry_creates_learning_log(tmp_path):
    registry_root = tmp_path / "knowledge_registry"
    os.environ["KNOWLEDGE_REGISTRY_PATH"] = str(registry_root)

    module_dir = tmp_path / "generated" / "hospital_management"
    module_dir.mkdir(parents=True, exist_ok=True)
    file_path = module_dir / "__init__.py"
    file_path.write_text("# generated module", encoding="utf-8")
    manifest_path = module_dir / "manifest.py"
    manifest_path.write_text("{ 'name': 'Hospital Management' }", encoding="utf-8")

    job_id = "test-job-001"
    prompt = "Generate a hospital management module"
    modules = [
        {
            "module_name": "hospital_management",
            "module_description": "Hospital management module",
            "depends": ["base"],
            "models": [],
            "matched_components": ["hospital_management/v1.0"],
        }
    ]
    module_paths = [str(module_dir)]
    append_learning_entry(
        job_id=job_id,
        prompt=prompt,
        modules=modules,
        module_paths=module_paths,
        matched_components=["hospital_management/v1.0"],
        notes=["Initial learning entry"],
    )

    learning_log_path = registry_root / "learning_log.json"
    assert learning_log_path.exists()

    content = json.loads(learning_log_path.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    assert len(content) == 1

    entry = content[0]
    assert entry["job_id"] == job_id
    assert entry["prompt"] == prompt
    assert entry["matched_components"] == ["hospital_management/v1.0"]
    assert entry["notes"] == ["Initial learning entry"]
    assert entry["modules"][0]["module_name"] == "hospital_management"
    generated_files = entry["modules"][0]["generated_files"]
    assert any(file["path"] == "hospital_management/__init__.py" for file in generated_files)
    assert any(file["path"] == "hospital_management/manifest.py" for file in generated_files)

    del os.environ["KNOWLEDGE_REGISTRY_PATH"]
