import os
import time
import uuid
import shutil
import httpx
import json
import asyncio
import logging
import traceback
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.models.schemas import GeneratorPayload
from app.generators.OdooModuleGenerator import OdooModuleGenerator
from app.services.zip_handler import ZipHandler
from app.services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo AI Module Generator",
    description="API to generate Odoo modules from JSON configuration",
    version="1.0.0"
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
    status: str          # "pending" | "running" | "done" | "error"
    progress: int        # 0-100
    message: str
    elapsed_sec: float
    estimated_remaining_sec: Optional[float] = None
    download_url: Optional[str] = None
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
        "error": j["error"],
    }


# ── Background tasks ─────────────────────────

async def _run_generate_module_job(job_id: str, payload: GeneratorPayload):
    """Background worker for /generate-module/"""
    try:
        _update_job(job_id, status="running", progress=5,
                    message="Parsing module config...",
                    estimated_total_sec=10)
        await asyncio.sleep(0)   # yield to event loop

        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            _update_job(job_id, status="error", progress=0,
                        error="No modules specified in configuration")
            return

        generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
        module_paths = []
        total = len(modules)

        for i, config_data in enumerate(modules):
            pct = 10 + int(80 * i / total)
            _update_job(job_id, progress=pct,
                        message=f"Generating module {i+1}/{total}: {config_data.get('module_name', '?')}...")
            await asyncio.sleep(0)

            module_path = await asyncio.to_thread(
                generator.generate_module, config_data, OUTPUT_DIR
            )
            module_paths.append(module_path)

        _update_job(job_id, progress=90, message="Creating ZIP archive...")
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

        _update_job(job_id, status="done", progress=100,
                    message="Done! Download your module below.",
                    download_url=f"/download/{job_id}")
        # store zip path for download
        jobs[job_id]["_zip_path"] = zip_path
        jobs[job_id]["_zip_name"] = zip_name

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update_job(job_id, status="error", progress=0,
                    error=str(exc))


async def _run_analyze_requirements_job(job_id: str, user_prompt: str):
    """Background worker for /analyze-requirements/"""
    try:
        _update_job(job_id, status="running", progress=5,
                    message="Sending prompt to AI...",
                    estimated_total_sec=45)   # AI calls can take ~30-45 s
        await asyncio.sleep(0)

        payload = await asyncio.to_thread(
            ai_service.analyze_requirements, user_prompt
        )

        _update_job(job_id, progress=60, message="AI finished — generating files...")
        await asyncio.sleep(0)

        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            _update_job(job_id, status="error",
                        error="No modules analyzed from the prompt")
            return

        generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
        module_paths = []
        total = len(modules)

        for i, config_data in enumerate(modules):
            pct = 60 + int(30 * i / total)
            _update_job(job_id, progress=pct,
                        message=f"Generating module {i+1}/{total}: {config_data.get('module_name', '?')}...")
            await asyncio.sleep(0)

            module_path = await asyncio.to_thread(
                generator.generate_module, config_data, OUTPUT_DIR
            )
            module_paths.append(module_path)

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

        _update_job(job_id, status="done", progress=100,
                    message="Done! Download your module below.",
                    download_url=f"/download/{job_id}")
        jobs[job_id]["_zip_path"] = zip_path
        jobs[job_id]["_zip_name"] = zip_name

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update_job(job_id, status="error", progress=0,
                    error=str(exc))


# ── Exception Handlers ───────────────────────

@app.exception_handler(httpx.ConnectError)
async def http_connect_error_handler(request: Request, exc: httpx.ConnectError):
    logger.error(f"HTTP Connect Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error_type": "NETWORK_ERROR",
            "message": "Could not connect to an external service. Please check network connectivity.",
            "debug_details": str(exc)
        },
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
    logger.error(f"JSON Decode Error: {exc}")
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
    logger.error(f"OS Error (File System): {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "STORAGE_ERROR",
            "message": "A file system error occurred. Please try again or contact support.",
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
            "message": "An unexpected error occurred. Please try again later.",
            "debug_details": traceback.format_exc()
        },
    )


# ── Routes ───────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Welcome to Odoo AI Module Generator API. Use /docs for documentation."}


# ── NEW: job-based endpoints ──────────────────

@app.post(
    "/generate-module/",
    response_model=JobStatus,
    summary="Generate module (async with progress)",
    description=(
        "Submit a module config and get back a **job_id**. "
        "Poll `/job/{job_id}` to see progress and remaining time. "
        "Download from `/download/{job_id}` when status is `done`."
    ),
)
async def generate_module(payload: GeneratorPayload, background_tasks=None):
    """
    Returns a job_id immediately. Use GET /job/{job_id} to track progress.
    """
    from fastapi import BackgroundTasks
    job_id = _new_job()
    # Use asyncio.create_task so the job runs in the background
    asyncio.create_task(_run_generate_module_job(job_id, payload))
    return _job_status_response(job_id)


@app.post(
    "/analyze-requirements/",
    response_model=JobStatus,
    summary="AI-analyze prompt and generate module (async with progress)",
    description=(
        "Submit a natural-language prompt. The server calls the AI in the background. "
        "Poll `/job/{job_id}` for **progress %** and **estimated remaining seconds**. "
        "Download the ZIP from `/download/{job_id}` when done."
    ),
)
async def analyze_requirements_and_generate(user_prompt: UserPrompt):
    """
    Returns a job_id immediately. Use GET /job/{job_id} to track progress.
    AI calls usually take 30-60 seconds.
    """
    job_id = _new_job()
    asyncio.create_task(_run_analyze_requirements_job(job_id, user_prompt.prompt))
    return _job_status_response(job_id)


@app.get(
    "/job/{job_id}",
    response_model=JobStatus,
    summary="Poll job status + remaining time",
    description=(
        "Returns current **progress** (0-100%), **elapsed_sec**, and "
        "**estimated_remaining_sec**. Keep polling every 2-3 seconds until "
        "`status` is `done` or `error`."
    ),
)
async def get_job_status(job_id: str):
    """
    Poll this endpoint after starting a generation job.
    - progress: 0-100
    - estimated_remaining_sec: countdown in seconds (null until job starts)
    - status: pending → running → done / error
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return _job_status_response(job_id)


@app.get(
    "/job/{job_id}/stream",
    summary="Stream job progress as Server-Sent Events (SSE)",
    description=(
        "An SSE stream that pushes a JSON event every 2 seconds until the job finishes. "
        "Useful for JavaScript `EventSource` clients. In Swagger, use `/job/{job_id}` polling instead."
    ),
)
async def stream_job_progress(job_id: str):
    """
    Server-Sent Events stream. Each event is a JSON object identical to
    the /job/{job_id} response. The stream closes when status is done or error.
    """
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
    summary="Download the generated ZIP when job is done",
)
async def download_result(job_id: str):
    """
    Available only when /job/{job_id} returns status=done.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = jobs[job_id]
    if j["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"Job is not done yet (status={j['status']})"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)