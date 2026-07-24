import os
import json
import logging
from typing import Any, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

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

    def upsert_generation_job(self, job_id: str, status: str, progress: int, message: str, module_config: Optional[dict], schema_preview: Optional[dict], zip_url: Optional[str] = None, github_url: Optional[str] = None, chat_history: Optional[list[dict]] = None) -> None:
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
