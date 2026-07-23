from fastapi.testclient import TestClient

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
