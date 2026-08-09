import os
import time
import uuid
import httpx
import json
import asyncio
import logging
import traceback
import shutil
import io
import zipfile
import re
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from pydantic import BaseModel
from typing import List, Optional

from app.models.schemas import ComponentRegistryEntry, GeneratorPayload, ChatMessage, ChatRequest, ChatResponse
from app.generators.OdooModuleGenerator import OdooModuleGenerator
from app.services.zip_handler import ZipHandler
from app.services.ai_service import AIService
from app.services.git_deploy_service import GitDeployService
from app.services.rag_service import RAGService
from app.services.component_registry_service import ComponentRegistryService
from app.services.learning_loop_service import append_learning_entry
from app.services.supabase_service import supabase_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
redis_url = os.getenv("REDIS_URL")
if redis_url:
    logger.info("REDIS_URL loaded successfully for backend cache integration.")
else:
    logger.info("REDIS_URL is not configured; Redis cache will remain disabled.")

app = FastAPI(
    title="Odoo AI Module Generator",
    description="API to generate Odoo modules from JSON configuration",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event() -> None:
    global jobs
    try:
        if redis_url:
            # FastAPICache expects raw bytes from Redis when decoding cached responses.
            # Using decode_responses=False avoids fastapi-cache decode issues with str values.
            redis_client = aioredis.from_url(redis_url, decode_responses=False)
            await redis_client.ping()
            FastAPICache.init(RedisBackend(redis_client), prefix="odoo_cache")
            logger.info("FastAPICache initialized with Redis backend.")
        synced_jobs = _load_jobs()
        if synced_jobs:
            jobs = synced_jobs
        else:
            jobs = {}
        _save_jobs()
    except Exception as exc:
        logger.exception("Startup job sync failed: %s", exc)

frontend_origins = []
for raw_origin in os.getenv("FRONTEND_URL", "http://localhost:5173").split(","):
    origin = raw_origin.strip()
    if origin:
        frontend_origins.append(origin)

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

ai_service = AIService(redis_url=redis_url)
rag_service = RAGService(redis_url=redis_url)
component_registry_service = ComponentRegistryService()


def _is_initial_greeting(content: str) -> bool:
    normalized = re.sub(r"[^a-zA-Z\u0600-\u06FF\s]", " ", content or "").strip().lower()
    if not normalized:
        return False
    greetings = {
        "hi", "hello", "hey", "hey there", "hi there", "hello there", "salut", "heyya",
        "اهلا", "اهلاً", "اهلا وسهلا", "اهلا ومرحبا", "مرحبا", "مرحباً", "السلام عليكم",
        "thanks", "thank you", "thx", "شكرا", "شاكر", "شكرا جزيلا"
    }
    return normalized in greetings or normalized.startswith("hello ") or normalized.startswith("hi ")


def _build_initial_greeting_reply(preferred_language: Optional[str]) -> ChatResponse:
    if preferred_language == "arabic":
        reply = (
            "أهلاً بك! أنا مساعدك التقني لبناء موديولات Odoo، وسأساعدك في تصميم الوحدة خطوة بخطوة بشكل احترافي وسهل. 🚀\n\n"
            "لنبدأ بالخطوة الأولى: ما هو الاسم التقني للوحدة `module name` الذي ترغب في إعطائه؟\n"
            "يرجى استخدام صيغة `snake_case` مع بداية حرف صغير، مثل `purchase_extension` أو `hr_custom`."
        )
    else:
        reply = (
            "Welcome! I'm your Odoo Module Architect, and I'm excited to help you build your next module. 🚀\n\n"
            "To get started, what is the technical name you'd like to give this module?\n"
            "Please use `snake_case` with a lowercase starting character, for example `purchase_extension` or `hr_custom`."
        )
    return ChatResponse(reply=reply, ready_to_generate=False, requirements_summary="")


def _persist_job_to_supabase(job_id: str, job_data: dict) -> None:
    if not supabase_service.is_enabled():
        return
    try:
        supabase_service.upsert_generation_job(
            job_id=job_id,
            status=job_data.get("status", "pending"),
            progress=int(job_data.get("progress", 0)),
            message=job_data.get("message", ""),
            module_config=job_data.get("module_config"),
            schema_preview=job_data.get("schema_preview"),
            zip_url=job_data.get("download_url"),
            github_url=job_data.get("github_url"),
        )
    except Exception as exc:
        logger.exception("Supabase persistence failed for job %s: %s", job_id, exc)


def _load_jobs() -> dict:
    local_jobs = {}
    if os.path.exists(JOBS_STATE_PATH):
        try:
            with open(JOBS_STATE_PATH, "r", encoding="utf-8") as f:
                local_jobs = json.load(f)
        except Exception:
            local_jobs = {}

    if supabase_service.is_enabled():
        try:
            rows = supabase_service.get_generation_jobs()
            if rows:
                normalized_jobs = {}
                for row in rows:
                    job_id = row.get("job_id")
                    if not job_id:
                        continue
                    local_job = local_jobs.get(job_id, {})
                    normalized_jobs[job_id] = {
                        "status": row.get("status") or "pending",
                        "progress": int(row.get("progress", 0) or 0),
                        "message": row.get("message", ""),
                        "started_at": row.get("started_at") or time.time(),
                        "estimated_total_sec": row.get("estimated_total_sec"),
                        "download_url": row.get("download_url") or row.get("zip_url"),
                        "github_url": row.get("github_url"),
                        "error": row.get("error"),
                        "schema_preview": row.get("schema_preview"),
                        "module_config": row.get("module_config"),
                        "chat_history": row.get("chat_history"),
                        "_module_paths": local_job.get("_module_paths") or [],
                        "_zip_path": local_job.get("_zip_path"),
                        "_zip_name": local_job.get("_zip_name"),
                    }
                # Supabase is the source of truth: only include jobs present in Supabase.
                # Preserve local artifact paths when available so we can serve files without re-downloading.
                return normalized_jobs
        except Exception as exc:
            logger.exception("Failed to load jobs from Supabase: %s", exc)

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

    for job_id, job_data in jobs.items():
        _persist_job_to_supabase(job_id, job_data)


jobs: dict = _load_jobs()

TEXT_EXTENSIONS = {".py", ".xml", ".csv", ".js", ".css", ".html", ".md", ".txt", ".json"}


class UserPrompt(BaseModel):
    prompt: str
    job_id: Optional[str] = None
    odoo_version: Optional[str] = None


class ModuleConfigSyncRequest(BaseModel):
    module_config: Optional[dict] = None
    schema_preview: Optional[dict] = None
    odoo_version: Optional[str] = None


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


def _new_job(job_id: Optional[str] = None) -> str:
    assigned_id = job_id or str(uuid.uuid4())

    jobs[assigned_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "started_at": time.time(),
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
    _save_jobs()
    return assigned_id


def _update_job(job_id: str, **kwargs):
    if job_id in jobs:
        jobs[job_id].update(kwargs)
        _save_jobs()


def _stage_label(progress: int) -> str:
    if progress <= 25:
        return 'Analyzing Requirements'
    if progress <= 50:
        return 'Architecting Odoo Schema'
    if progress <= 85:
        return 'Generating Python & XML Code'
    return 'Finalizing & Packaging Module'


def _ensure_job_loaded(job_id: str) -> Optional[dict]:
    if job_id in jobs:
        return jobs[job_id]

    try:
        job_data = supabase_service.get_generation_job(job_id)
    except Exception as exc:
        logger.exception("Failed to restore job %s from Supabase: %s", job_id, exc)
        return None

    if not job_data:
        return None

    jobs[job_id] = {
        "status": job_data.get("status") or "pending",
        "progress": int(job_data.get("progress", 0) or 0),
        "message": job_data.get("message", ""),
        "started_at": time.time(),
        "estimated_total_sec": None,
        "download_url": job_data.get("download_url") or job_data.get("zip_url"),
        "github_url": job_data.get("github_url"),
        "error": job_data.get("error"),
        "schema_preview": job_data.get("schema_preview"),
        "module_config": job_data.get("module_config"),
        "_module_paths": [],
        "_zip_path": None,
        "_zip_name": None,
    }
    _save_jobs()
    return jobs[job_id]


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

    progress = int(j["progress"])
    message = j["message"]
    if j["status"] not in ("error", "pending") and progress > 0:
        message = _stage_label(progress)

    return {
        "job_id": job_id,
        "status": j["status"],
        "progress": progress,
        "message": message,
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


def _collect_files_from_zip(zip_path: str) -> list:
    files = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext not in TEXT_EXTENSIONS:
                    continue
                try:
                    with zf.open(name) as fh:
                        content = fh.read().decode("utf-8", errors="replace")
                except Exception:
                    continue
                files.append({"name": os.path.basename(name), "path": name.replace("\\", "/"), "content": content})
    except Exception:
        logger.exception("Failed to collect files from zip: %s", zip_path)
    return sorted(files, key=lambda x: x["path"])


def _collect_files_from_zip_url(url: str) -> list:
    files = []
    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content), "r") as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext not in TEXT_EXTENSIONS:
                    continue
                try:
                    with zf.open(name) as fh:
                        content = fh.read().decode("utf-8", errors="replace")
                except Exception:
                    continue
                files.append({"name": os.path.basename(name), "path": name.replace("\\", "/"), "content": content})
    except Exception:
        logger.exception("Failed to collect files from zip URL: %s", url)
    return sorted(files, key=lambda x: x["path"])


def _derive_zip_name_from_url(download_url: str, job_id: str) -> str:
    if not download_url:
        return f"{job_id}.zip"
    zip_name = os.path.basename(download_url.split("?")[0]) or f"{job_id}.zip"
    if not zip_name.lower().endswith(".zip"):
        zip_name = f"{zip_name}.zip"
    return zip_name


def _restore_job_artifacts(job_id: str) -> bool:
    job = jobs.get(job_id)
    if not job:
        return False

    module_paths = job.get("_module_paths") or []
    for module_path in module_paths:
        if module_path and os.path.exists(module_path):
            return True

    zip_path = _get_zip_path_for_job(job)
    if zip_path:
        return True

    download_url = job.get("download_url")
    if download_url:
        return _save_job_zip_from_url(job_id, download_url)

    return False


def _get_zip_path_for_job(job: dict) -> Optional[str]:
    zip_path = job.get("_zip_path")
    if zip_path and os.path.exists(zip_path):
        return zip_path

    zip_name = job.get("_zip_name")
    if zip_name:
        candidate = os.path.join(OUTPUT_DIR, zip_name)
        if os.path.exists(candidate):
            return candidate
    return None


def _save_job_zip_from_url(job_id: str, download_url: str) -> bool:
    try:
        if download_url.startswith("/"):
            download_url = f"http://127.0.0.1:8000{download_url}"

        response = httpx.get(download_url, timeout=30.0)
        response.raise_for_status()

        zip_name = _derive_zip_name_from_url(download_url, job_id)

        zip_path = os.path.join(OUTPUT_DIR, zip_name)
        with open(zip_path, "wb") as f:
            f.write(response.content)

        extract_dir = os.path.join(OUTPUT_DIR, f"{job_id}_extracted")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        module_paths = []
        for entry in sorted(os.listdir(extract_dir)):
            entry_path = os.path.join(extract_dir, entry)
            if os.path.isdir(entry_path):
                module_paths.append(entry_path)
        if not module_paths:
            module_paths = [extract_dir]

        jobs[job_id]["_zip_path"] = zip_path
        jobs[job_id]["_zip_name"] = zip_name
        jobs[job_id]["_module_paths"] = module_paths
        _save_jobs()
        return True
    except Exception:
        logger.exception("Failed to download and restore ZIP for job %s from %s", job_id, download_url)
        return False


def _delete_job_artifacts(job_id: str) -> None:
    job = jobs.get(job_id)
    if not job:
        return

    zip_path = job.get("_zip_path")
    if zip_path and os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except OSError:
            logger.exception("Failed to remove ZIP file for job %s", job_id)

    module_paths = job.get("_module_paths") or []
    for module_path in module_paths:
        if module_path and os.path.exists(module_path):
            try:
                shutil.rmtree(module_path)
            except OSError:
                logger.exception("Failed to remove module path for job %s: %s", job_id, module_path)


def _delete_job(job_id: str) -> bool:
    if job_id in jobs:
        _delete_job_artifacts(job_id)
        try:
            del jobs[job_id]
            _save_jobs()
        except Exception:
            logger.exception("Failed to delete job from memory: %s", job_id)
            return False
        return True

    return False


def _deploy_to_github(module_paths: list, repository_urls: Optional[list[str]] = None) -> list[str]:
    git_service = GitDeployService()
    urls = []
    for index, module_path in enumerate(module_paths):
        repo_url = None
        repo_name = None
        if repository_urls and index < len(repository_urls):
            repo_url = repository_urls[index]
            if repo_url:
                repo_name = repo_url.rstrip('/').split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
        url = git_service.deploy(module_path, repo_name=repo_name, owner=_extract_github_owner(repo_url) if repo_url else None)
        urls.append(url)
    return urls


def _extract_github_owner(repository_url: Optional[str]) -> Optional[str]:
    if not repository_url:
        return None
    try:
        cleaned = repository_url.strip().rstrip('/')
        parts = cleaned.split('/')
        if len(parts) >= 2:
            owner = parts[-2]
            if owner.lower() == 'github.com':
                return None
            return owner
    except Exception:
        return None
    return None


async def _generate_and_deploy(job_id: str, modules: list, ai_done_progress: int = 10, prompt: Optional[str] = None):
    generator = OdooModuleGenerator(templates_dir=TEMPLATES_DIR)
    module_paths = []
    total = len(modules)
    deploy_target = modules[0].get("git_deploy_target", "local_zip") if modules else "local_zip"

    try:
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
            repository_urls = [
                module.get("repository_url")
                for module in modules
                if isinstance(module, dict)
            ]
            _update_job(job_id, progress=88, message="Pushing to GitHub... (this may take a moment)")
            await asyncio.sleep(0)
            try:
                github_urls = await asyncio.to_thread(_deploy_to_github, module_paths, repository_urls)
                _update_job(
                    job_id,
                    status="done",
                    progress=100,
                    message="Done! Module(s) pushed to GitHub.",
                    github_url=", ".join(github_urls),
                )
                try:
                    append_learning_entry(
                        job_id=job_id,
                        prompt=prompt,
                        modules=modules,
                        module_paths=module_paths,
                        matched_components=sorted({
                            comp
                            for module in modules
                            if isinstance(module, dict)
                            for comp in (module.get("matched_components") or [])
                        }),
                        notes=["Generated module pushed to GitHub."],
                    )
                except Exception:
                    logger.exception("Failed to append learning log for job %s", job_id)
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
            err = "Failed to create ZIP file"
            _update_job(job_id, status="error", message=err, error=err)
            return

        jobs[job_id]["_zip_path"] = zip_path
        jobs[job_id]["_zip_name"] = zip_name

        zip_url = None
        try:
            if supabase_service.is_enabled():
                zip_url = supabase_service.upload_zip("modules", zip_path, zip_name)
        except Exception as exc:
            logger.exception("ZIP upload to Supabase failed: %s", exc)

        _update_job(
            job_id,
            status="done",
            progress=100,
            message="Done! Your module is ready.",
            download_url=zip_url or f"/download/{job_id}",
        )
        try:
            append_learning_entry(
                job_id=job_id,
                prompt=prompt,
                modules=modules,
                module_paths=module_paths,
                matched_components=sorted({
                    comp
                    for module in modules
                    if isinstance(module, dict)
                    for comp in (module.get("matched_components") or [])
                }),
                notes=["Generated module packaged as ZIP."],
            )
        except Exception:
            logger.exception("Failed to append learning log for job %s", job_id)
    except Exception as exc:
        logger.exception("Generation pipeline failed for job %s", job_id)
        err = str(exc).strip() or "Generation failed"
        if not err.lower().startswith(("generation failed", "zip", "module generation")):
            err = f"Generation failed: {err}"
        _update_job(job_id, status="error", progress=0, message=err, error=err)


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

        version = (payload_data.get("odoo_version") or "17.0").strip() or "17.0"
        for module in modules:
            if isinstance(module, dict):
                module.setdefault("odoo_version", version)

        _update_job(
            job_id,
            progress=10,
            message="Schema ready — generating files...",
            module_config=modules[0] if len(modules) == 1 else {"modules": modules},
            schema_preview=_build_schema_preview(modules),
        )
        await asyncio.sleep(0)

        await _generate_and_deploy(job_id, modules, ai_done_progress=10, prompt=None)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        err_msg = str(exc)
        _update_job(job_id, status="error", progress=0, message=err_msg, error=err_msg)


async def _run_analyze_requirements_job(job_id: str, user_prompt: str, odoo_version: Optional[str] = None):
    try:
        _update_job(
            job_id,
            status="running",
            progress=5,
            message="Sending prompt to AI...",
            estimated_total_sec=60,
        )
        await asyncio.sleep(0)

        payload = await ai_service.analyze_requirements(user_prompt, odoo_version, job_id=job_id)

        payload_data = payload.model_dump()
        modules = payload_data.get("modules", [])
        if not modules:
            err = "No modules analyzed from the prompt"
            _update_job(job_id, status="error", progress=0, message=err, error=err)
            return

        version = (odoo_version or payload_data.get("odoo_version") or "17.0").strip() or "17.0"
        for module in modules:
            if isinstance(module, dict):
                module.setdefault("odoo_version", version)

        # Attach matched registry component IDs to module configs so the generator can merge docs/security
        try:
            matching_components = ai_service._find_matching_components(user_prompt) if hasattr(ai_service, '_find_matching_components') else []
            matched_ids = [c.component_id for c in matching_components] if matching_components else []
            if matched_ids:
                for module in modules:
                    if isinstance(module, dict):
                        module.setdefault('matched_components', matched_ids)
        except Exception:
            # non-fatal: proceed without matched components
            matched_ids = []

        _update_job(
            job_id,
            progress=55,
            message="AI finished — drawing system architecture...",
            module_config=modules[0] if len(modules) == 1 else {"modules": modules},
            schema_preview=_build_schema_preview(modules),
        )
        await asyncio.sleep(0)

        await _generate_and_deploy(job_id, modules, ai_done_progress=55, prompt=user_prompt)
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

    if len(request.messages) == 1 and _is_initial_greeting(last.content):
        return _build_initial_greeting_reply(request.preferred_language)

    payload = [{"role": m.role, "content": m.content} for m in request.messages]
    language_hint = None
    if request.preferred_language == "arabic":
        language_hint = (
            "Reply in Arabic using a warm, professional Odoo architect tone. Be concise and technically precise. "
            "For every new session, begin with a warm professional greeting and a short introduction, then ask only the first question: the module's technical name. If the user's message is only a greeting or a trivial opening such as hi, hello, اهلا, or thanks, also reply with a warm professional welcome and ask only that first question. Do not mention the full discovery flow yet. "
            "Ask exactly ONE main question at a time and follow an incremental flow. After each user answer, acknowledge it briefly with positive feedback and ask only the next logical question. "
            "If the answer is vague, ask one short clarifying question before moving on. "
            "Use clean Markdown with backticks for all technical names such as model names, field names, module names, XML IDs, and method names. "
            "Keep one blank line between sections, and preserve punctuation and numbers in their natural positions in RTL text. "
            "If the user writes in English, still answer in Arabic."
        )
    elif request.preferred_language == "english":
        language_hint = (
            "Reply in English with a warm, professional Odoo architect tone. Be concise and technically precise. "
            "For every new session, begin with a warm professional greeting and a short introduction, then ask only the first question: the module's technical name. If the user's message is only a greeting or a trivial opening such as hi, hello, أهلا, or thanks, also reply with a warm professional welcome and ask only that first question. Do not mention the full discovery flow yet. "
            "Ask exactly ONE main question at a time and follow an incremental flow. After each user answer, acknowledge it briefly with positive feedback and ask only the next logical question. "
            "If the answer is vague, ask one short clarifying question before moving on. "
            "Use clean Markdown with backticks for all technical names such as model names, field names, module names, XML IDs, and method names. "
            "Keep one blank line between sections. If the user writes in Arabic, still answer in English."
        )

    try:
        if request.job_id:
            existing_job = supabase_service.get_generation_job(request.job_id)
            current_chat = existing_job.get("chat_history") if existing_job else []
            chat_history = current_chat or []
            if not isinstance(chat_history, list):
                chat_history = []
            next_messages = [
                {"role": item.role, "content": item.content}
                for item in request.messages
            ]
            combined_chat = chat_history + next_messages
            payload_for_ai = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in combined_chat]
            if language_hint:
                payload_for_ai.insert(0, {"role": "system", "content": language_hint})
            if existing_job and existing_job.get("module_config"):
                payload_for_ai.append({
                    "role": "system",
                    "content": "Current module configuration context:\n" + json.dumps(existing_job.get("module_config"), ensure_ascii=False),
                })
            response = await ai_service.chat_requirements(payload_for_ai, job_id=request.job_id)
            supabase_service.upsert_generation_job(
                job_id=request.job_id,
                status=existing_job.get("status", "running") if existing_job else "running",
                progress=existing_job.get("progress", 0) if existing_job else 0,
                message=existing_job.get("message", "") if existing_job else "",
                module_config=existing_job.get("module_config") if existing_job else None,
                schema_preview=existing_job.get("schema_preview") if existing_job else None,
                chat_history=combined_chat,
            )
        else:
            if language_hint:
                payload.insert(0, {"role": "system", "content": language_hint})
            response = await ai_service.chat_requirements(payload, job_id=request.job_id)

        for item in request.messages:
            supabase_service.insert_chat_message(None, item.role, item.content)
        return response
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
    provided_id = getattr(payload, 'job_id', None)
    job_id = _new_job(provided_id)
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
    job_id = _new_job(user_prompt.job_id)
    asyncio.create_task(_run_analyze_requirements_job(job_id, user_prompt.prompt, user_prompt.odoo_version))
    return _job_status_response(job_id)


@app.api_route("/job/{job_id}/sync-config", methods=["POST", "PATCH"])
async def sync_job_config(job_id: str, payload: ModuleConfigSyncRequest):
    restored_job = _ensure_job_loaded(job_id)
    if not restored_job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    jobs[job_id]["module_config"] = payload.module_config
    jobs[job_id]["schema_preview"] = payload.schema_preview or jobs[job_id].get("schema_preview")
    if payload.odoo_version:
        jobs[job_id]["odoo_version"] = payload.odoo_version
    jobs[job_id]["message"] = "Changes synced to cloud successfully"
    _save_jobs()

    if supabase_service.is_enabled():
        supabase_service.update_generation_job(
            job_id,
            module_config=payload.module_config,
            schema_preview=payload.schema_preview or jobs[job_id].get("schema_preview"),
            message=jobs[job_id]["message"],
        )

    return {
        "job_id": job_id,
        "status": "ok",
        "message": jobs[job_id]["message"],
    }


@app.get("/history")
async def get_history():
    jobs_list = supabase_service.get_generation_jobs()
    chat_list = supabase_service.get_chat_history()

    # Return all jobs by job_id. Deletion is performed by job_id, so history
    # should not collapse separate records with the same module name.
    return {
        "jobs": jobs_list,
        "chat_history": chat_list,
    }


def _usage_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        text = str(value).strip().replace("Z", "+00:00")
        return datetime.fromisoformat(text).strftime("%Y-%m-%d")
    except Exception:
        text = str(value).strip()
        return text[:10] if len(text) >= 10 else None


def _row_model_name(row: dict) -> str:
    model_name = row.get("model_name")
    if model_name is None:
        return "unknown"
    return str(model_name).strip() or "unknown"


def _compute_quota_stats(today_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Compute daily quota usage for every model defined in the `model_quotas` table.

    - `limit_type = "requests"`: compare today's request count against `daily_limit`
    - `limit_type = "tokens"`: compare today's `total_tokens` sum against `daily_limit`

    "Today" is derived from the `created_at` timestamp of the logs (UTC day boundary),
    so usage resets automatically each day.

    Returns a tuple of:
      - `models`: per-model intelligence cards data (model_name, today_usage, success_rate,
        remaining_quota, unit, percent_used)
      - `quota_status`: per-model quota row (model_name, current_usage, limit, unit, percent_used)
    """
    quotas = supabase_service.get_model_quotas()
    if not quotas:
        return [], []

    today_usage: dict[str, dict] = {}
    for row in today_rows:
        model_name = _row_model_name(row)
        try:
            total_tokens = int(row.get("total_tokens") or 0)
        except (TypeError, ValueError):
            total_tokens = 0
        is_success = str(row.get("status") or "success").strip() == "success"
        entry = today_usage.setdefault(model_name, {"requests": 0, "success": 0, "tokens": 0})
        entry["requests"] += 1
        entry["tokens"] += total_tokens
        if is_success:
            entry["success"] += 1

    models: list[dict] = []
    quota_status: list[dict] = []
    for quota in quotas:
        model_name = str(quota.get("model_name") or "").strip()
        limit_type = str(quota.get("limit_type") or "requests").strip().lower()
        try:
            daily_limit = float(quota.get("daily_limit") or 0)
        except (TypeError, ValueError):
            daily_limit = 0
        if not model_name or daily_limit <= 0:
            continue
        usage = today_usage.get(model_name, {"requests": 0, "success": 0, "tokens": 0})
        if limit_type == "tokens":
            current_usage = usage.get("tokens", 0)
            unit = "Tokens"
        else:
            current_usage = usage.get("requests", 0)
            unit = "Requests"
        total_calls = usage.get("requests", 0)
        success_rate = round((usage.get("success", 0) / total_calls) * 100, 2) if total_calls > 0 else 0.0
        percent_used = round((current_usage / daily_limit) * 100, 2)
        models.append({
            "model_name": model_name,
            "today_usage": current_usage,
            "success_rate": success_rate,
            "remaining_quota": int(daily_limit) - current_usage,
            "unit": unit,
            "percent_used": percent_used,
        })
        quota_status.append({
            "model_name": model_name,
            "current_usage": current_usage,
            "limit": int(daily_limit),
            "unit": unit,
            "percent_used": percent_used,
        })
    return models, quota_status


@app.get(
    "/api/stats/usage",
    summary="Daily token usage aggregated by provider and model",
    description=(
        "Returns usage metrics from the `api_usage_logs` table aggregated by day "
        "and grouped by `provider_name` and `model_name`, ready for the 'Usage Over Time' "
        "line charts and 'Token Distribution by Model' views. Pass an optional `model` "
        "query parameter to filter by model name; read `model_names` for the distinct "
        "models in the window and `models_breakdown` for per-model totals.\n\n"
        "The `models` array holds Model Intelligence Card data for every quota-tracked "
        "model: `model_name`, `today_usage` (Tokens or Requests per `limit_type`), "
        "`success_rate`, `remaining_quota` (`daily_limit` - today's usage), `unit` and "
        "`percent_used`. The `quota_status` array mirrors the same computation. Usage is "
        "counted against today's `created_at` boundary, so it resets automatically each day."
    ),
)
async def get_usage_stats(days: int = 30, model: Optional[str] = None):
    if not supabase_service.is_enabled():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"success": False, "message": "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY."},
        )

    normalized_model = model.strip() if model else None
    rows = supabase_service.get_usage_logs(days=days, model=normalized_model)

    model_names: dict[str, bool] = {}
    if normalized_model:
        all_rows = supabase_service.get_usage_logs(days=days)
        for row in all_rows:
            model_names[_row_model_name(row)] = True
    else:
        for row in rows:
            model_names[_row_model_name(row)] = True

    model_providers: dict[str, dict[str, int]] = {}
    daily: dict[str, dict] = {}
    for row in rows:
        date_str = _usage_date(row.get("created_at"))
        if not date_str:
            continue
        provider_name = row.get("provider_name") or "unknown"
        model_name = _row_model_name(row)
        is_success = str(row.get("status") or "success").strip() == "success"
        try:
            prompt_tokens = int(row.get("prompt_tokens") or 0)
            completion_tokens = int(row.get("completion_tokens") or 0)
            total_tokens = int(row.get("total_tokens") or (prompt_tokens + completion_tokens))
        except (TypeError, ValueError):
            prompt_tokens = completion_tokens = total_tokens = 0

        model_provider_counts = model_providers.setdefault(model_name, {})
        model_provider_counts[provider_name] = model_provider_counts.get(provider_name, 0) + 1

        day = daily.setdefault(date_str, {"date": date_str, "requests": 0, "success": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "providers": {}, "models": {}})
        day["requests"] += 1
        if is_success:
            day["success"] += 1
        day["prompt_tokens"] += prompt_tokens
        day["completion_tokens"] += completion_tokens
        day["total_tokens"] += total_tokens

        provider_entry = day["providers"].setdefault(provider_name, {"requests": 0, "success": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        provider_entry["requests"] += 1
        if is_success:
            provider_entry["success"] += 1
        provider_entry["prompt_tokens"] += prompt_tokens
        provider_entry["completion_tokens"] += completion_tokens
        provider_entry["total_tokens"] += total_tokens

        model_entry = day["models"].setdefault(model_name, {"requests": 0, "success": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        model_entry["requests"] += 1
        if is_success:
            model_entry["success"] += 1
        model_entry["prompt_tokens"] += prompt_tokens
        model_entry["completion_tokens"] += completion_tokens
        model_entry["total_tokens"] += total_tokens

    daily_list = sorted(daily.values(), key=lambda item: item["date"])

    totals = {"requests": 0, "success": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "providers": {}, "models": {}}
    for day in daily_list:
        totals["requests"] += day["requests"]
        totals["success"] += day["success"]
        totals["prompt_tokens"] += day["prompt_tokens"]
        totals["completion_tokens"] += day["completion_tokens"]
        totals["total_tokens"] += day["total_tokens"]
        for provider_name, entry in day["providers"].items():
            provider_total = totals["providers"].setdefault(provider_name, {"requests": 0, "success": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            for key in ("requests", "success", "prompt_tokens", "completion_tokens", "total_tokens"):
                provider_total[key] += entry[key]
        for model_name, entry in day["models"].items():
            model_total = totals["models"].setdefault(model_name, {"requests": 0, "success": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            for key in ("requests", "success", "prompt_tokens", "completion_tokens", "total_tokens"):
                model_total[key] += entry[key]

    models_breakdown = {}
    for model_name, entry in totals["models"].items():
        counts = model_providers.get(model_name, {})
        provider_name = max(counts, key=counts.get) if counts else "unknown"
        models_breakdown[model_name] = {**entry, "provider": provider_name}

    quota_models, quota_status = _compute_quota_stats(supabase_service.get_usage_logs_today())

    return {
        "success": True,
        "days": days,
        "model": model,
        "models": quota_models,
        "model_names": sorted(model_names.keys()),
        "models_breakdown": models_breakdown,
        "quota_status": quota_status,
        "daily": daily_list,
        "totals": totals,
    }


@app.delete(
    "/api/stats/usage/test-data",
    summary="Delete test usage logs",
    description=(
        "Deletes all rows in `api_usage_logs` whose `provider_name` matches the given value "
        "(defaults to `test_usage_tracking`), so test-only entries can be cleared and the "
        "dashboard shows only real AI usage. Returns the number of deleted rows."
    ),
)
async def clear_test_usage_data(provider: str = "test_usage_tracking"):
    if not supabase_service.is_enabled():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"success": False, "message": "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY."},
        )
    deleted = supabase_service.delete_usage_logs_by_provider(provider)
    return {"success": True, "deleted": deleted, "provider": provider}


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


@app.get("/job/{job_id}/restore")
async def restore_job(job_id: str):
    local_job = _ensure_job_loaded(job_id) or {}
    job_data = None
    if supabase_service.is_enabled():
        job_data = supabase_service.get_generation_job(job_id)

    if not local_job and not job_data:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    module_config = local_job.get("module_config") if local_job.get("module_config") is not None else (job_data.get("module_config") if job_data else None)
    chat_history = (job_data.get("chat_history") if job_data else []) or []
    return {
        "job_id": job_id,
        "status": local_job.get("status") or (job_data.get("status") if job_data else None) or "pending",
        "progress": local_job.get("progress") if local_job.get("progress") is not None else (job_data.get("progress") if job_data else 0) or 0,
        "message": local_job.get("message") if local_job.get("message") is not None else (job_data.get("message") if job_data else "") or "",
        "chat_history": chat_history,
        "module_config": module_config,
        "schema_preview": local_job.get("schema_preview") if local_job.get("schema_preview") is not None else (job_data.get("schema_preview") if job_data else None),
    }

@app.delete(
    "/job/{job_id}",
    summary="Delete a saved job and its generated artifacts",
)
async def delete_job(job_id: str):
    if not supabase_service.is_enabled() and job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    supabase_deleted = True
    if supabase_service.is_enabled():
        supabase_deleted = supabase_service.delete_generation_job(job_id)

    local_deleted = _delete_job(job_id)
    if local_deleted:
        _save_jobs()

    if supabase_service.is_enabled() and not supabase_deleted:
        raise HTTPException(status_code=500, detail=f"Job '{job_id}' could not be deleted from remote history")

    if not local_deleted and not supabase_deleted:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return {"status": "ok", "message": f"Job '{job_id}' deleted"}


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
    if module_paths:
        return {"files": _collect_files_from_paths(module_paths)}

    if _restore_job_artifacts(job_id):
        module_paths = j.get("_module_paths") or []
        if module_paths:
            return {"files": _collect_files_from_paths(module_paths)}
        zip_path = _get_zip_path_for_job(j)
        if zip_path:
            files = _collect_files_from_zip(zip_path)
            if files:
                return {"files": files}

    raise HTTPException(status_code=404, detail="No generated files found for this job")


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
        download_url = j.get("download_url")
        if download_url and _save_job_zip_from_url(job_id, download_url):
            zip_path = _get_zip_path_for_job(j)
            zip_name = j.get("_zip_name", zip_name)
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found on server")
    return FileResponse(
        path=zip_path,
        filename=zip_name,
        media_type="application/x-zip-compressed",
    )


@app.get("/components", response_model=List[ComponentRegistryEntry])
def list_components():
    try:
        return component_registry_service.list_components()
    except ValueError as exc:
        logger.exception("Component registry metadata error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
