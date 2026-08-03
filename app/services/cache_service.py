import hashlib
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import redis
except Exception as exc:  # pragma: no cover - dependency optional at runtime
    redis = None
    logger.warning("redis package unavailable: %s", exc)


class RedisCacheService:
    """Small Redis-backed cache wrapper for AI and RAG responses."""

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 1800) -> None:
        self.redis_url = (redis_url or os.getenv("REDIS_URL") or "").strip()
        self.default_ttl = int(default_ttl or 1800)
        self._client = None
        self._enabled = False
        self._initialize()

    def _initialize(self) -> None:
        if not self.redis_url or redis is None:
            self._enabled = False
            if not self.redis_url:
                logger.info("Redis cache disabled because REDIS_URL is not configured.")
            else:
                logger.warning("Redis cache disabled because the redis package is not available.")
            return

        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=False,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            self._client.ping()
            self._enabled = True
            logger.info("Redis cache is enabled using REDIS_URL.")
        except Exception as exc:  # pragma: no cover - runtime environment dependent
            self._enabled = False
            logger.warning("Redis cache unavailable; continuing without cache: %s", exc)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    @staticmethod
    def _build_key(prefix: str, raw_payload: str) -> str:
        digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
        return f"odoo:{prefix}:{digest}"

    def build_key(self, prefix: str, raw_payload: str) -> str:
        return self._build_key(prefix, raw_payload)

    def get_json(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        try:
            raw = self._client.get(key)
            if raw is None:
                return None
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8")
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Redis cache GET failed for %s: %s", key, exc)
            return None

    def set_json(self, key: str, payload: Any, ttl: Optional[int] = None) -> bool:
        if not self.enabled:
            return False
        try:
            self._client.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl or self.default_ttl)
            return True
        except Exception as exc:
            logger.warning("Redis cache SET failed for %s: %s", key, exc)
            return False
