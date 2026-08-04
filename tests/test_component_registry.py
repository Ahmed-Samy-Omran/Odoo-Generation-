import json

import pytest

from app.services.component_registry_service import ComponentRegistryService


def test_list_components_reads_valid_metadata(tmp_path):
    component_dir = tmp_path / "auth_component"
    component_dir.mkdir()
    metadata = {
        "name": "Auth Component",
        "version": "1.0.0",
        "description": "Authentication knowledge component for user session management.",
        "capabilities": [
            "user_authentication",
            "session_management",
            "token_validation",
        ],
        "author": "Coregen",
        "tags": ["security", "authentication", "user"],
    }
    (component_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    service = ComponentRegistryService(registry_dir=str(tmp_path))
    components = service.list_components()

    assert len(components) == 1
    assert components[0].component_id == "auth_component"
    assert components[0].metadata.name == "Auth Component"
    assert "token_validation" in components[0].metadata.capabilities


def test_list_components_raises_for_invalid_metadata_json(tmp_path):
    component_dir = tmp_path / "invalid_component"
    component_dir.mkdir()
    (component_dir / "metadata.json").write_text("{invalid json}", encoding="utf-8")

    service = ComponentRegistryService(registry_dir=str(tmp_path))

    with pytest.raises(ValueError):
        service.list_components()


def test_list_components_returns_empty_for_missing_registry(tmp_path):
    service = ComponentRegistryService(registry_dir=str(tmp_path / "missing_registry"))
    assert service.list_components() == []
