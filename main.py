import os
import time
import uuid
import httpx
import json
import asyncio
import logging
import traceback
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.models.schemas import GeneratorPayload, ChatMessage, ChatRequest, ChatResponse
from app.generators.OdooModuleGenerator import OdooModuleGenerator
from app.services.zip_handler import ZipHandler
from app.services.ai_service import AIService
from app.services.git_deploy_service import GitDeployService
from app.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo AI Module Generator",
    description="API to generate Odoo modules from JSON configuration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "generated_modules")
JOBS_STATE_PATH = os.path.join(BASE_DIR, "jobs_state.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

ai_service = AIService()
rag_service = RAGService()


def _load_jobs() -> dict:
    if not os.path.exists(JOBS_STATE_PATH):
        return {}

    try:
        with open(JOBS_STATE_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except Exception:
        return {}

    for job in loaded.values():
        if job.get("status") in ("pending", "running"):
            job["status"] = "error"
            job["message"] = "Server restarted while job was running. Please resubmit."
            job["error"] = "SERVER_RESTART"
    return loaded


def _save_jobs() -> None:
    try:
        with open(JOBS_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
    except OSError:
        logger.exception("Failed to save job state")


jobs: dict = _load_jobs()

TEXT_EXTENSIONS = {".py", ".xml", ".csv", ".js", ".css", ".html", ".md", ".txt", ".json"}


class UserPrompt(BaseModel):
    prompt: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    elapsed_sec: float
    estimated_remaining_sec: Optional[float] = None
    download_url: Optional[str] = None
    github_url: Optional[str] = None
    error: Optional[str] = None
    schema_preview: Optional[dict] = None


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
        "schema_preview": None,
        "_module_paths": [],
        "_zip_path": None,
        "_zip_name": None,
    }
    _save_jobs()
    return job_id


def _update_job(job_id: str, **kwargs):
    if job_id in jobs:
        jobs[job_id].update(kwargs)
        _save_jobs()


def _build_schema_preview(modules: list) -> dict:
    """Build ERD + use-case preview data for frontend diagram animation."""
    models_out = []
    use_cases = []
    actors = {"User", "Administrator"}

    for module in modules:
        module_name = module.get("module_name", "Module")
        for model in module.get("models", []):
            model_name = model.get("name", "")
            fields = []
            for field in model.get("fields", []):
                fields.append({
                    "name": field.get("name"),
                    "type": field.get("type"),
                    "required": bool(field.get("required", False)),
                    "relation": field.get("relation"),
                })
            models_out.append({
                "name": model_name,
                "module_name": module_name,
                "description": model.get("description", ""),
                "fields": fields,
            })
            for action in ("Create", "View", "Edit"):
                use_cases.append({
                    "name": f"{action} {model_name}",
                    "actor": "User",
                    "model": model_name,
                })
            use_cases.append({
                "name": f"Delete {model_name}",
                "actor": "Administrator",
                "model": model_name,
            })

        for group in module.get("security_groups") or []:
            if group.get("name"):
                actors.add(group["name"])

        for menu in module.get("menus") or []:
            if menu.get("name"):
                use_cases.append({
                    "name": menu["name"],
                    "actor": "Administrator" if not menu.get("parent_xml_id") else "User",
                })

        for action in module.get("actions") or []:
            if action.get("name"):
                use_cases.append({
                    "name": action["name"],
                    "actor": "User",
                    "model": action.get("res_model"),
                })

    return {
        "module_name": modules[0].get("module_name", "Module") if modules else "Module",
        "models": models_out,
        "actors": sorted(actors),
        "use_cases": use_cases,
    }


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
        "schema_preview": j.get("schema_preview"),
    }


def _collect_files_from_paths(module_paths: list) -> list:
    files = []
    for module_path in module_paths:
        module_name = os.path.basename(module_path)
        for root, _, filenames in os.walk(module_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in TEXT_EXTENSIONS:
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, module_path).replace("\\", "/")
                path = f"{module_name}/{rel_path}"
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except OSError:
                    continue
                files.append({"name": filename, "path": path, "content": content})
    return sorted(files, key=lambda x: x["path"])


def _deploy_to_github(module_paths: list) -> list[str]:
    git_service = GitDeployService()
    urls = []
    for module_path in module_paths:
        url = git_service.deploy(module_path)
        urls.append(url)
    return urls


async def _generate_and_deploy(job_id: str, modules: list, ai_done_progress: int = 10):
    generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
    module_paths = []
    total = len(modules)
    deploy_target = modules[0].get("git_deploy_target", "local_zip") if modules else "local_zip"

    for i, config_data in enumerate(modules):
        pct = ai_done_progress + int((85 - ai_done_progress) * i / total)
        _update_job(
            job_id,
            progress=pct,
            message=f"Generating module {i + 1}/{total}: {config_data.get('module_name', '?')}...",
        )
        await asyncio.sleep(0)
        module_path = await asyncio.to_thread(generator.generate_module, config_data, OUTPUT_DIR)
        module_paths.append(module_path)

    jobs[job_id]["_module_paths"] = module_paths

    if deploy_target == "github":
        _update_job(job_id, progress=88, message="Pushing to GitHub... (this may take a moment)")
        await asyncio.sleep(0)
        try:
            github_urls = await asyncio.to_thread(_deploy_to_github, module_paths)
            _update_job(
                job_id,
                status="done",
                progress=100,
                message="Done! Module(s) pushed to GitHub.",
                github_url=", ".join(github_urls),
            )
        except EnvironmentError as exc:
            err = f"GitHub config error: {exc}"
            _update_job(job_id, status="error", progress=0, message=err, error=err)
        except Exception as exc:
            logger.exception("GitHub deploy failed for job %s", job_id)
            err = f"GitHub deploy failed: {exc}"
            _update_job(job_id, status="error", progress=0, message=err, error=err)
        return

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
        _update_job(job_id, status="error", message="Failed to create ZIP file", error="Failed to create ZIP file")
        return

    jobs[job_id]["_zip_path"] = zip_path
    jobs[job_id]["_zip_name"] = zip_name
    _update_job(
        job_id,
        status="done",
        progress=100,
        message="Done! Your module is ready.",
        download_url=f"/download/{job_id}",
    )


async def _run_generate_module_job(job_id: str, payload: GeneratorPayload):
    try:
        _update_job(
            job_id,
            status="running",
            progress=5,
            message="Parsing module config...",
            estimated_total_sec=15,
        )
        await asyncio.sleep(0)

        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            err = "No modules specified in configuration"
            _update_job(job_id, status="error", progress=0, message=err, error=err)
            return

        _update_job(
            job_id,
            progress=10,
            message="Schema ready — generating files...",
            schema_preview=_build_schema_preview(modules),
        )
        await asyncio.sleep(0)

        await _generate_and_deploy(job_id, modules, ai_done_progress=10)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        err_msg = str(exc)
        _update_job(job_id, status="error", progress=0, message=err_msg, error=err_msg)


async def _run_analyze_requirements_job(job_id: str, user_prompt: str):
    try:
        _update_job(
            job_id,
            status="running",
            progress=5,
            message="Sending prompt to AI...",
            estimated_total_sec=60,
        )
        await asyncio.sleep(0)

        payload = await asyncio.to_thread(ai_service.analyze_requirements, user_prompt)

        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            err = "No modules analyzed from the prompt"
            _update_job(job_id, status="error", progress=0, message=err, error=err)
            return

        _update_job(
            job_id,
            progress=55,
            message="AI finished — drawing system architecture...",
            schema_preview=_build_schema_preview(modules),
        )
        await asyncio.sleep(0)

        await _generate_and_deploy(job_id, modules, ai_done_progress=55)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        err_msg = str(exc)
        _update_job(job_id, status="error", progress=0, message=err_msg, error=err_msg)


@app.exception_handler(httpx.ConnectError)
async def http_connect_error_handler(request: Request, exc: httpx.ConnectError):
    logger.error(f"HTTP Connect Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error_type": "NETWORK_ERROR",
            "message": "Could not connect to an external service. Please check network connectivity.",
            "debug_details": str(exc),
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
            "debug_details": str(exc),
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
            "debug_details": str(exc),
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
            "debug_details": traceback.format_exc(),
        },
    )


@app.get("/")
def read_root():
    return {"message": "Welcome to Odoo AI Module Generator API. Use /docs for documentation."}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/rag/index")
def index_rag_documents(reset: bool = False):
    try:
        result = rag_service.index_directory(reset=reset)
        return JSONResponse(status_code=200, content=result)
    except Exception as exc:
        logger.exception("RAG indexing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/rag/search")
def search_rag_documents(query: str, top_k: int = 3):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    results = rag_service.search(query, top_k=top_k)
    return {"query": query, "results": results}


@app.post("/chat/", response_model=ChatResponse)
async def chat_requirements(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="At least one message is required")

    last = request.messages[-1]
    if last.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from the user")

    payload = [{"role": m.role, "content": m.content} for m in request.messages]
    try:
        return await asyncio.to_thread(ai_service.chat_requirements, payload)
    except Exception as exc:
        logger.exception("Chat failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
    "/job/{job_id}/files",
    summary="List generated files for a completed job",
    description="Returns the list of generated files for completed jobs.",
)
async def get_job_files(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = jobs[job_id]
    if j["status"] != "done":
        raise HTTPException(status_code=409, detail=f"Job is not done yet (status={j['status']})")
    module_paths = j.get("_module_paths") or []
    if not module_paths:
        raise HTTPException(status_code=404, detail="No generated files found for this job")
    return {"files": _collect_files_from_paths(module_paths)}


@app.get(
    "/download/{job_id}",
    summary="Download the generated ZIP (local_zip jobs only)",
)
async def download_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = jobs[job_id]
    if j["status"] != "done":
        raise HTTPException(status_code=409, detail=f"Job is not done yet (status={j['status']})")
    if j.get("github_url"):
        raise HTTPException(status_code=400, detail=f"This job was deployed to GitHub: {j['github_url']}")
    zip_path = j.get("_zip_path")
    zip_name = j.get("_zip_name", "module.zip")
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found on server")
    return FileResponse(
        path=zip_path,
        filename=zip_name,
        media_type="application/x-zip-compressed",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
