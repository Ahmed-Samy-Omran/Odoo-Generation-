import asyncio

import main


def test_sync_job_config_updates_jobs_and_supabase(monkeypatch):
    job_id = "test-sync-job"
    main.jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "",
        "started_at": 0,
        "estimated_total_sec": None,
        "download_url": None,
        "github_url": None,
        "error": None,
        "schema_preview": None,
        "module_config": None,
        "_module_paths": [],
        "_zip_path": None,
        "_zip_name": None,
    }

    captured = {}

    def fake_update_generation_job(job_id_value, **kwargs):
        captured["job_id"] = job_id_value
        captured["kwargs"] = kwargs

    monkeypatch.setattr(main.supabase_service, "is_enabled", lambda: True)
    monkeypatch.setattr(main.supabase_service, "update_generation_job", fake_update_generation_job)

    payload = main.ModuleConfigSyncRequest(
        module_config={"module_name": "demo_module", "models": []},
        schema_preview={"module_name": "demo_module", "models": [], "actors": [], "use_cases": []},
    )

    response = asyncio.run(main.sync_job_config(job_id, payload))

    assert response["job_id"] == job_id
    assert main.jobs[job_id]["module_config"]["module_name"] == "demo_module"
    assert main.jobs[job_id]["schema_preview"]["module_name"] == "demo_module"
    assert captured["job_id"] == job_id
    assert captured["kwargs"]["module_config"]["module_name"] == "demo_module"


def test_sync_job_config_recovers_missing_job_from_supabase(monkeypatch):
    job_id = "test-recover-job"
    main.jobs.pop(job_id, None)

    captured = {}

    def fake_get_generation_job(job_id_value):
        if job_id_value == job_id:
            return {
                "status": "running",
                "progress": 10,
                "message": "existing",
                "module_config": {"module_name": "restored_module"},
                "schema_preview": {"module_name": "restored_module", "models": [], "actors": [], "use_cases": []},
            }
        return None

    def fake_update_generation_job(job_id_value, **kwargs):
        captured["job_id"] = job_id_value
        captured["kwargs"] = kwargs

    monkeypatch.setattr(main.supabase_service, "is_enabled", lambda: True)
    monkeypatch.setattr(main.supabase_service, "get_generation_job", fake_get_generation_job)
    monkeypatch.setattr(main.supabase_service, "update_generation_job", fake_update_generation_job)

    payload = main.ModuleConfigSyncRequest(
        module_config={"module_name": "new_module", "models": []},
        schema_preview={"module_name": "new_module", "models": [], "actors": [], "use_cases": []},
    )

    response = asyncio.run(main.sync_job_config(job_id, payload))

    assert response["job_id"] == job_id
    assert main.jobs[job_id]["module_config"]["module_name"] == "new_module"
    assert main.jobs[job_id]["schema_preview"]["module_name"] == "new_module"
    assert captured["job_id"] == job_id
