import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx
from dotenv import load_dotenv
from supabase import create_client, Client

logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

class SupabaseService:
    def __init__(self) -> None:
        self.client: Optional[Client] = None
        self.enabled = bool(SUPABASE_URL and SUPABASE_KEY)
        if self.enabled:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as exc:
                logger.exception("Failed to initialize Supabase client: %s", exc)
                self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled and self.client is not None

    def verify_supabase_token(self, access_token: str) -> Optional[dict]:
        """Validate a Supabase session access token via ``GET /auth/v1/user``.

        Returns ``{"id": <user id>, "email": <email>}`` when the token is valid,
        otherwise ``None``. No anon key is required; the user's own access token
        is sent as the Bearer credential.
        """
        if not self.enabled or not access_token:
            return None
        try:
            response = httpx.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15,
            )
            if response.status_code != 200:
                return None
            data = response.json()
            user_id = data.get("id")
            if not user_id:
                return None
            return {"id": user_id, "email": data.get("email") or ""}
        except Exception as exc:
            logger.exception("Supabase token verification failed: %s", exc)
            return None

    def insert_chat_message(self, user_id: Optional[str], role: str, content: str) -> None:
        if not self.is_enabled():
            return
        try:
            self.client.table("chat_history").insert({
                "user_id": user_id,
                "role": role,
                "content": content,
            }).execute()
        except Exception as exc:
            logger.exception("Supabase chat insert failed: %s", exc)

    def log_api_usage(self, provider_name: str, model_name: str, prompt_tokens: int, completion_tokens: int, total_tokens: int, status: str, job_id: Optional[str] = None, estimated: bool = False, user_id: Optional[str] = None) -> None:
        if not self.is_enabled():
            return
        try:
            data = {
                "provider_name": provider_name,
                "model_name": model_name,
                "prompt_tokens": int(prompt_tokens or 0),
                "completion_tokens": int(completion_tokens or 0),
                "total_tokens": int(total_tokens or 0),
                "status": status,
            }
            if user_id is not None:
                data["user_id"] = user_id
            if job_id:
                data["job_id"] = job_id
            if estimated:
                data["error_message"] = "estimated:true"
            self.client.table("api_usage_logs").insert(data).execute()
        except Exception as exc:
            logger.exception("Supabase usage log insert failed: %s", exc)

    def get_usage_logs(self, days: int = 30, model: Optional[str] = None, user_id: Optional[str] = None) -> list[dict]:
        if not self.is_enabled():
            return []
        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
            query = self.client.table("api_usage_logs").select("*").gte("created_at", since)
            if model:
                query = query.eq("model_name", model.strip())
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.order("created_at", desc=True).execute()
            return getattr(result, "data", []) or []
        except Exception as exc:
            logger.exception("Supabase usage log fetch failed: %s", exc)
            return []

    def delete_usage_logs_by_provider(self, provider_name: str) -> int:
        if not self.is_enabled():
            return 0
        try:
            result = self.client.table("api_usage_logs").delete().eq("provider_name", provider_name).execute()
            return len(getattr(result, "data", []) or [])
        except Exception as exc:
            logger.exception("Supabase usage log delete failed: %s", exc)
            return 0

    def get_usage_logs_today(self, user_id: Optional[str] = None) -> list[dict]:
        if not self.is_enabled():
            return []
        try:
            since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
            query = self.client.table("api_usage_logs").select("*").gte("created_at", since)
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.execute()
            return getattr(result, "data", []) or []
        except Exception as exc:
            logger.exception("Supabase today usage fetch failed: %s", exc)
            return []

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Fetch the caller's role and token limit from ``public.profiles``.

        Returns ``{"role": ..., "token_limit": ...}`` or ``None`` when the
        profile does not exist yet (the DB trigger normally creates it).
        """
        if not self.is_enabled() or not user_id:
            return None
        try:
            result = self.client.table("profiles").select("role", "token_limit").eq("id", user_id).maybe_single().execute()
            return getattr(result, "data", None)
        except Exception as exc:
            logger.exception("Supabase profile fetch failed for %s: %s", user_id, exc)
            return None

    def get_user_usage_today(self, user_id: str) -> dict:
        """Aggregate a user's token/request consumption for the current day.

        Returns ``{"tokens": int, "requests": int}`` summed from
        ``api_usage_logs`` where ``user_id`` matches and ``created_at`` falls
        on today's UTC boundary.
        """
        if not self.is_enabled() or not user_id:
            return {"tokens": 0, "requests": 0}
        try:
            since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
            result = self.client.table("api_usage_logs").select("total_tokens").eq("user_id", user_id).gte("created_at", since).execute()
            rows = getattr(result, "data", []) or []
            total_tokens = 0
            for row in rows:
                try:
                    total_tokens += int(row.get("total_tokens") or 0)
                except (TypeError, ValueError):
                    continue
            return {"tokens": total_tokens, "requests": len(rows)}
        except Exception as exc:
            logger.exception("Supabase per-user daily usage failed for %s: %s", user_id, exc)
            return {"tokens": 0, "requests": 0}

    def get_model_quotas(self) -> list[dict]:
        if not self.is_enabled():
            return []
        try:
            result = self.client.table("model_quotas").select("*").execute()
            return getattr(result, "data", []) or []
        except Exception as exc:
            logger.exception("Supabase model quotas fetch failed: %s", exc)
            return []

    def upsert_generation_job(self, job_id: str, status: str, progress: int, message: str, module_config: Optional[dict], schema_preview: Optional[dict], zip_url: Optional[str] = None, github_url: Optional[str] = None, chat_history: Optional[list[dict]] = None, user_id: Optional[str] = None) -> None:
        if not self.is_enabled():
            return
        try:
            data = {
                "job_id": job_id,
                "status": status,
                "progress": progress,
                "message": message,
                "module_config": module_config,
                "schema_preview": schema_preview,
            }
            if user_id is not None:
                data["user_id"] = user_id
            if zip_url is not None:
                data["zip_url"] = zip_url
            if github_url is not None:
                data["github_url"] = github_url
            if chat_history is not None:
                data["chat_history"] = chat_history
            self.client.table("generation_jobs").upsert(data, on_conflict="job_id").execute()
        except Exception as exc:
            logger.exception("Supabase job upsert failed: %s", exc)


    def delete_generation_job(self, job_id: str) -> bool:
        if not self.is_enabled():
            return False
        try:
            self.client.table("generation_jobs").delete().eq("job_id", job_id).execute()
            return True
        except Exception as exc:
            logger.exception("Supabase job delete failed: %s", exc)
            return False

    def update_generation_job(self, job_id: str, **kwargs: Any) -> None:
        if not self.is_enabled():
            return
        try:
            self.client.table("generation_jobs").update(kwargs).eq("job_id", job_id).execute()
        except Exception as exc:
            logger.exception("Supabase job update failed: %s", exc)

    def get_generation_jobs(self, user_id: Optional[str] = None) -> list[dict]:
        if not self.is_enabled():
            return []
        try:
            query = self.client.table("generation_jobs").select("*").order("created_at", desc=True)
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.execute()
            rows = getattr(result, "data", []) or []
            deduped = {}
            for row in rows:
                job_id = row.get("job_id")
                if not job_id:
                    continue
                if job_id not in deduped:
                    deduped[job_id] = row
            return list(deduped.values())
        except Exception as exc:
            logger.exception("Supabase history fetch failed: %s", exc)
            return []

    def get_generation_job(self, job_id: str) -> Optional[dict]:
        if not self.is_enabled():
            return None
        try:
            result = self.client.table("generation_jobs").select("*").eq("job_id", job_id).maybe_single().execute()
            return getattr(result, "data", None)
        except Exception as exc:
            logger.exception("Supabase job fetch failed: %s", exc)
            return None

    def get_chat_history(self, user_id: Optional[str] = None) -> list[dict]:
        if not self.is_enabled():
            return []
        try:
            query = self.client.table("chat_history").select("*").order("created_at", desc=True)
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.execute()
            rows = getattr(result, "data", []) or []
            return rows
        except Exception as exc:
            logger.exception("Supabase chat history fetch failed: %s", exc)
            return []

    def upload_zip(self, bucket_name: str, file_path: str, file_name: str) -> Optional[str]:
        if not self.is_enabled():
            return None
        try:
            with open(file_path, "rb") as fh:
                response = self.client.storage.from_(bucket_name).upload(file_name, fh, file_options={"content-type": "application/zip", "upsert": "true"})
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_name)
            return public_url
        except Exception as exc:
            logger.exception("Supabase storage upload failed: %s", exc)
            return None

supabase_service = SupabaseService()
