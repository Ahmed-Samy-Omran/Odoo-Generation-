"""Shared helper for dev scripts that talk to the Odoo Generator HTTP API.

The API is JWT-protected, so each script authenticates once via
``POST /api/auth/login`` (credentials come from ``ADMIN_USERNAME`` /
``ADMIN_PASSWORD`` in ``.env``) and reuses the Bearer token for every request.
"""
import os
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "http://127.0.0.1:8000"

_token_cache: dict[str, str] = {}
_token_lock = threading.Lock()


def _credentials() -> tuple[str, str]:
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not password:
        raise RuntimeError(
            "ADMIN_PASSWORD is not set in .env; configure login credentials first."
        )
    return username, password


def get_token(base_url: str = DEFAULT_BASE_URL) -> str:
    """Return a cached access token for the given API base URL."""
    base_url = base_url.rstrip("/")
    with _token_lock:
        cached = _token_cache.get(base_url)
        if cached:
            return cached
        username, password = _credentials()
        response = requests.post(
            f"{base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=15,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Login failed ({response.status_code}): {response.text[:300]}"
            )
        token = response.json()["access_token"]
        _token_cache[base_url] = token
        return token


def auth_headers(base_url: str = DEFAULT_BASE_URL) -> dict:
    """Headers carrying the Bearer token, for use with ``requests``."""
    return {"Authorization": f"Bearer {get_token(base_url)}"}


def session(base_url: str = DEFAULT_BASE_URL) -> requests.Session:
    """A ``requests.Session`` pre-authenticated for the given API base URL."""
    http_session = requests.Session()
    http_session.headers.update(auth_headers(base_url))
    return http_session
