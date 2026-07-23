import asyncio
import os

import main


def test_generate_and_deploy_reports_zip_creation_errors(monkeypatch, tmp_path):
    job_id = "zip-error-job"
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

    def fake_generate_module(self, config, output_dir):
        return str(tmp_path / config["module_name"])

    def fake_create_batch_zip(module_paths, zip_path):
        raise RuntimeError("zip creation exploded")

    monkeypatch.setattr(main.supabase_service, "is_enabled", lambda: False)
    monkeypatch.setattr(main.OdooModuleGenerator, "generate_module", fake_generate_module)
    monkeypatch.setattr(main.ZipHandler, "create_batch_zip", fake_create_batch_zip)

    modules = [{"module_name": "demo_module", "models": []}]

    asyncio.run(main._generate_and_deploy(job_id, modules, ai_done_progress=10))

    assert main.jobs[job_id]["status"] == "error"
    assert "zip creation exploded" in main.jobs[job_id]["message"]
    assert main.jobs[job_id]["error"] == main.jobs[job_id]["message"]
