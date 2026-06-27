import os
import time
import uuid
import httpx
import json
import asyncio
import logging
import traceback
import zipfile
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.models.schemas import GeneratorPayload
from app.generators.OdooModuleGenerator import OdooModuleGenerator
from app.services.zip_handler import ZipHandler
from app.services.ai_service import AIService
from app.services.git_deploy_service import GitDeployService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo AI Module Generator",
    description="API to generate Odoo modules from JSON configuration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "generated_modules")

os.makedirs(OUTPUT_DIR, exist_ok=True)

ai_service = AIService()

# ─────────────────────────────────────────────
# In-memory job store  {job_id: {...}}
# ─────────────────────────────────────────────
jobs: dict = {}


class UserPrompt(BaseModel):
    prompt: str


class JobStatus(BaseModel):
    job_id: str
    status: str                              # pending | running | done | error
    progress: int                            # 0-100
    message: str
    elapsed_sec: float
    estimated_remaining_sec: Optional[float] = None
    download_url: Optional[str] = None      # set only for local_zip result
    github_url: Optional[str] = None        # set only for github result
    error: Optional[str] = None


# ── helpers ──────────────────────────────────

def _new_job() -> str:
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "started_at": time.time(),
        "estimated_total_sec": None,
        "download_url": None,
        "github_url": None,
        "error": None,
    }
    return job_id


def _update_job(job_id: str, **kwargs):
    if job_id in jobs:
        jobs[job_id].update(kwargs)


def _job_status_response(job_id: str) -> dict:
    j = jobs.get(job_id)
    if not j:
        return {}
    elapsed = time.time() - j["started_at"]
    est = None
    if j["progress"] and j["progress"] < 100 and j.get("estimated_total_sec"):
        est = max(0.0, j["estimated_total_sec"] - elapsed)
    return {
        "job_id": job_id,
        "status": j["status"],
        "progress": j["progress"],
        "message": j["message"],
        "elapsed_sec": round(elapsed, 1),
        "estimated_remaining_sec": round(est, 1) if est is not None else None,
        "download_url": j["download_url"],
        "github_url": j["github_url"],
        "error": j["error"],
    }


# ── Git deploy helper (runs in thread) ───────

def _deploy_to_github(module_paths: list) -> list[str]:
    """
    Push each module directory to its own GitHub repo.
    Returns list of GitHub HTML URLs.
    """
    git_service = GitDeployService()
    urls = []
    for module_path in module_paths:
        url = git_service.deploy(module_path)
        urls.append(url)
    return urls


# ── Core generation logic (shared by both endpoints) ─────────────────────────

async def _generate_and_deploy(
    job_id: str,
    modules: list,
    estimated_total_sec: float,
    start_progress: int = 5,
    ai_done_progress: int = 10,   # where we are when AI is done (or skipped)
):
    """
    Shared generation + optional GitHub deploy logic.
    Runs all CPU/IO work in threads so FastAPI stays non-blocking.
    """
    generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
    module_paths = []
    total = len(modules)

    # Determine deploy target (use first module's setting; all modules in one
    # request should share the same preference)
    deploy_target = modules[0].get("git_deploy_target", "local_zip") if modules else "local_zip"

    # ── Generate each module ──────────────────
    for i, config_data in enumerate(modules):
        pct = ai_done_progress + int((85 - ai_done_progress) * i / total)
        _update_job(job_id, progress=pct,
                    message=f"Generating module {i + 1}/{total}: "
                            f"{config_data.get('module_name', '?')}...")
        await asyncio.sleep(0)

        module_path = await asyncio.to_thread(
            generator.generate_module, config_data, OUTPUT_DIR
        )
        module_paths.append(module_path)

    # ── Deploy ───────────────────────────────
    if deploy_target == "github":
        _update_job(job_id, progress=88,
                    message="Pushing to GitHub... (this may take a moment)")
        await asyncio.sleep(0)

        try:
            github_urls = await asyncio.to_thread(_deploy_to_github, module_paths)
            github_summary = ", ".join(github_urls)
            _update_job(
                job_id,
                status="done",
                progress=100,
                message=f"Done! Module(s) pushed to GitHub.",
                github_url=github_summary,
            )
        except EnvironmentError as exc:
            # Missing GITHUB_TOKEN / GITHUB_USER → clear user-facing error
            _update_job(job_id, status="error", progress=0,
                        error=f"GitHub config error: {exc}")
        except Exception as exc:
            logger.exception("GitHub deploy failed for job %s", job_id)
            _update_job(job_id, status="error", progress=0,
                        error=f"GitHub deploy failed: {exc}")

    else:
        # ── Local ZIP ────────────────────────
        _update_job(job_id, progress=92, message="Creating ZIP archive...")
        await asyncio.sleep(0)

        zip_name = (
            f"{modules[0].get('module_name', 'custom_module')}_batch.zip"
            if len(modules) > 1
            else f"{modules[0].get('module_name', 'custom_module')}.zip"
        )
        zip_path = os.path.join(OUTPUT_DIR, zip_name)
        await asyncio.to_thread(ZipHandler.create_batch_zip, module_paths, zip_path)

        if not os.path.exists(zip_path):
            _update_job(job_id, status="error", error="Failed to create ZIP file")
            return

        jobs[job_id]["_zip_path"] = zip_path
        jobs[job_id]["_zip_name"] = zip_name
        _update_job(
            job_id,
            status="done",
            progress=100,
            message="Done! Download your module below.",
            download_url=f"/download/{job_id}",
        )


# ── Background tasks ─────────────────────────

async def _run_generate_module_job(job_id: str, payload: GeneratorPayload):
    """Background worker for /generate-module/"""
    try:
        _update_job(job_id, status="running", progress=5,
                    message="Parsing module config...",
                    estimated_total_sec=15)
        await asyncio.sleep(0)

        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            _update_job(job_id, status="error", progress=0,
                        error="No modules specified in configuration")
            return

        await _generate_and_deploy(
            job_id=job_id,
            modules=modules,
            estimated_total_sec=15,
            start_progress=5,
            ai_done_progress=10,
        )

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update_job(job_id, status="error", progress=0, error=str(exc))


async def _run_analyze_requirements_job(job_id: str, user_prompt: str):
    """Background worker for /analyze-requirements/"""
    try:
        _update_job(job_id, status="running", progress=5,
                    message="Sending prompt to AI...",
                    estimated_total_sec=60)
        await asyncio.sleep(0)

        payload = await asyncio.to_thread(
            ai_service.analyze_requirements, user_prompt
        )

        _update_job(job_id, progress=55, message="AI finished — generating files...")
        await asyncio.sleep(0)

        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            _update_job(job_id, status="error", progress=0,
                        error="No modules analyzed from the prompt")
            return

        await _generate_and_deploy(
            job_id=job_id,
            modules=modules,
            estimated_total_sec=60,
            start_progress=5,
            ai_done_progress=55,
        )

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update_job(job_id, status="error", progress=0, error=str(exc))


# ── Exception Handlers ───────────────────────

@app.exception_handler(httpx.ConnectError)
async def http_connect_error_handler(request: Request, exc: httpx.ConnectError):
    logger.error(f"HTTP Connect Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error_type": "NETWORK_ERROR",
            "message": "Could not connect to an external service.",
            "debug_details": str(exc)
        },
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "INVALID_JSON",
            "message": "The request body contains invalid JSON data.",
            "debug_details": str(exc)
        },
    )


@app.exception_handler(OSError)
async def os_error_handler(request: Request, exc: OSError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "STORAGE_ERROR",
            "message": "A file system error occurred.",
            "debug_details": str(exc)
        },
    )


@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "UNKNOWN_ERROR",
            "message": "An unexpected error occurred.",
            "debug_details": traceback.format_exc()
        },
    )


# ── Routes ───────────────────────────────────

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Odoo AI Module Generator API. Use /docs for documentation."
    }


@app.post(
    "/generate-module/",
    response_model=JobStatus,
    summary="Generate module from JSON config (async with progress)",
    description=(
        "Submit a module config. Returns a **job_id** immediately.\n\n"
        "- Set `git_deploy_target: 'github'` in any module to push it to GitHub "
        "(requires `GITHUB_TOKEN` + `GITHUB_USER` in `.env`).\n"
        "- Set `git_deploy_target: 'local_zip'` (default) to download a ZIP.\n\n"
        "Poll `/job/{job_id}` for progress. "
        "Download from `/download/{job_id}` (local_zip) or check `github_url` (github)."
    ),
)
async def generate_module(payload: GeneratorPayload):
    job_id = _new_job()
    asyncio.create_task(_run_generate_module_job(job_id, payload))
    return _job_status_response(job_id)


@app.post(
    "/analyze-requirements/",
    response_model=JobStatus,
    summary="AI-analyze prompt and generate module (async with progress)",
    description=(
        "Submit a natural-language prompt. The AI decides the module structure.\n\n"
        "Include phrases like **'push to github'** or **'deploy to github'** in your "
        "prompt and the AI will set `git_deploy_target: 'github'` automatically.\n\n"
        "Poll `/job/{job_id}` for progress and `estimated_remaining_sec`."
    ),
)
async def analyze_requirements_and_generate(user_prompt: UserPrompt):
    job_id = _new_job()
    asyncio.create_task(_run_analyze_requirements_job(job_id, user_prompt.prompt))
    return _job_status_response(job_id)


@app.get(
    "/job/{job_id}",
    response_model=JobStatus,
    summary="Poll job status + remaining time",
    description=(
        "Returns **progress** (0-100 %), **elapsed_sec**, and **estimated_remaining_sec**.\n\n"
        "Keep polling every 2-3 seconds until `status` is `done` or `error`.\n\n"
        "When done:\n"
        "- `download_url` is set if `git_deploy_target` was `local_zip`\n"
        "- `github_url` is set if `git_deploy_target` was `github`"
    ),
)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return _job_status_response(job_id)


@app.get(
    "/job/{job_id}/stream",
    summary="Stream job progress as Server-Sent Events",
    description="SSE stream — pushes a JSON event every 2 seconds until done/error.",
)
async def stream_job_progress(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    async def event_generator():
        while True:
            data = _job_status_response(job_id)
            yield f"data: {json.dumps(data)}\n\n"
            if data["status"] in ("done", "error"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get(
    "/download/{job_id}",
    summary="Download the generated ZIP (local_zip jobs only)",
)
async def download_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = jobs[job_id]
    if j["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"Job is not done yet (status={j['status']})"
        )
    if j.get("github_url"):
        raise HTTPException(
            status_code=400,
            detail=f"This job was deployed to GitHub: {j['github_url']}"
        )
    zip_path = j.get("_zip_path")
    zip_name = j.get("_zip_name", "module.zip")
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found on server")
    return FileResponse(
        path=zip_path,
        filename=zip_name,
        media_type="application/x-zip-compressed"
    )


@app.get(
    "/job/{job_id}/files",
    summary="List generated files for a completed job",
    description="Returns the list of generated files for completed local_zip jobs.",
)
async def get_job_files(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    j = jobs[job_id]
    if j["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"Job is not done yet (status={j['status']})"
        )
    if j.get("github_url"):
        raise HTTPException(
            status_code=400,
            detail=f"This job was deployed to GitHub: {j['github_url']}"
        )

    zip_path = j.get("_zip_path")
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found on server")

    try:
        files = []
        with zipfile.ZipFile(zip_path, "r") as zipf:
            for info in zipf.infolist():
                if not info.is_dir():
                    files.append({
                        "path": info.filename,
                        "name": os.path.basename(info.filename),
                        "content": zipf.read(info.filename).decode("utf-8", errors="replace"),
                    })
        return {"files": files}
    except zipfile.BadZipFile:
        raise HTTPException(status_code=500, detail="Failed to read ZIP archive")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)