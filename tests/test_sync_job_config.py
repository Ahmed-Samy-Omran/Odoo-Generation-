from fastapi.testclient import TestClient

import main
from main import app, jobs


def test_patch_sync_job_config_updates_job_state():
    client = TestClient(app)
    job_id = "test-sync-job"
    jobs[job_id] = {
        "status": "running",
        "progress": 10,
        "message": "Working",
        "schema_preview": None,
        "module_config": None,
    }

    response = client.patch(
        f"/job/{job_id}/sync-config",
        json={
            "module_config": {"module_name": "demo_module"},
            "schema_preview": {"module_name": "demo_module", "models": []},
        },
    )

    assert response.status_code == 200
    assert jobs[job_id]["module_config"]["module_name"] == "demo_module"
    assert jobs[job_id]["schema_preview"]["module_name"] == "demo_module"
    assert jobs[job_id]["message"] == "Changes synced to cloud successfully"


def test_restore_prefers_latest_local_job_state(monkeypatch):
    client = TestClient(app)
    job_id = "restore-prefers-local"
    jobs[job_id] = {
        "status": "done",
        "progress": 100,
        "message": "Latest local state",
        "schema_preview": {"module_name": "latest_module", "models": [{"name": "LatestModel", "fields": []}]},
        "module_config": {"module_name": "latest_module", "models": [{"name": "LatestModel", "fields": []}]},
    }

    monkeypatch.setattr(
        "main.supabase_service.get_generation_job",
        lambda _job_id: {
            "status": "running",
            "progress": 20,
            "message": "Older cloud state",
            "schema_preview": {"module_name": "stale_module", "models": []},
            "module_config": {"module_name": "stale_module", "models": []},
        },
    )

    response = client.get(f"/job/{job_id}/restore")

    assert response.status_code == 200
    assert response.json()["message"] == "Latest local state"
    assert response.json()["module_config"]["module_name"] == "latest_module"
    assert response.json()["schema_preview"]["module_name"] == "latest_module"


def test_analyze_requirements_endpoint_uses_odoo_version(monkeypatch):
    client = TestClient(app)
    job_id = "versioned-analysis"

    class FakePayload:
        def __init__(self, modules):
            self.modules = modules

        def model_dump(self):
            return {"modules": self.modules}

    def fake_analyze_requirements(user_prompt, odoo_version=None):
        assert user_prompt == "Build me a simple module"
        assert odoo_version == "16.0"
        return FakePayload([{"module_name": "demo_module", "models": []}])

    monkeypatch.setattr(main.ai_service, "analyze_requirements", fake_analyze_requirements)
    monkeypatch.setattr(main, "_generate_and_deploy", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "_save_jobs", lambda: None)

    response = client.post(
        "/analyze-requirements/",
        json={"prompt": "Build me a simple module", "job_id": job_id, "odoo_version": "16.0"},
    )

    assert response.status_code == 200
    assert response.json()["job_id"] == job_id
