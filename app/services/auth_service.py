import os
import base64
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "").strip()

try:
    JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "1440") or 1440)
except (TypeError, ValueError):
    JWT_EXPIRES_MINUTES = 1440

if not JWT_SECRET:
    JWT_SECRET = secrets.token_urlsafe(48)
    logger.warning(
        "JWT_SECRET is not set. Using a random per-process secret; tokens will be "
        "invalidated when the server restarts. Set JWT_SECRET in .env for production."
    )

ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_GUEST = "guest"


@dataclass
class CurrentUser:
    """Authenticated caller, built from the JWT payload.

    ``role`` is one of ``admin``, ``user`` or ``guest``. Anonymous Supabase
    sessions (no email / ``is_anonymous`` claim) are identified as ``guest``.
    """

    sub: str
    role: str = ROLE_USER
    email: Optional[str] = None

    @property
    def username(self) -> str:
        return self.email or self.sub

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_guest(self) -> bool:
        return self.role == ROLE_GUEST


def create_access_token(username: str, role: str = ROLE_USER, email: Optional[str] = None) -> str:
    """Issue a JWT carrying ``sub`` (the user id), ``role`` and optional ``email``.

    For the local admin login, ``username`` is the admin username and ``role`` is
    ``"admin"``. For Supabase users, ``username`` is the Supabase user id and
    ``role`` is ``"user"``.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role or ROLE_USER,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }
    if email:
        payload["email"] = email
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a token, returning ``{sub, role, email}`` or ``None``."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            return None
        return {
            "sub": sub,
            "role": payload.get("role", ROLE_USER) or ROLE_USER,
            "email": payload.get("email"),
        }
    except jwt.PyJWTError:
        return None


def authenticate_user(username: str, password: str) -> bool:
    """Local admin fallback: match ADMIN_USERNAME / ADMIN_PASSWORD from .env."""
    if not username or not password:
        return False
    if not ADMIN_PASSWORD:
        logger.warning("ADMIN_PASSWORD is not set; local admin login is disabled.")
        return False
    return username.strip() == ADMIN_USERNAME and password == ADMIN_PASSWORD


def verify_supabase_jwt(token: str) -> Optional[dict]:
    """Verify a Supabase Auth JWT directly using ``SUPABASE_JWT_SECRET``.

    Supabase signs tokens with HS256 using a base64url-encoded project secret.
    Returns ``{"sub": <user id>, "email": <email or None>, "is_anonymous": bool}``
    when the token is valid, otherwise ``None``.
    """
    if not SUPABASE_JWT_SECRET or not token:
        return None
    try:
        if len(SUPABASE_JWT_SECRET) < 32:
            secret = SUPABASE_JWT_SECRET.encode("utf-8")
        else:
            padded = SUPABASE_JWT_SECRET + "=" * (-len(SUPABASE_JWT_SECRET) % 4)
            secret = base64.urlsafe_b64decode(padded)
    except Exception:
        secret = SUPABASE_JWT_SECRET.encode("utf-8")

    for algorithm in ("HS256", "HS384", "HS512"):
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[algorithm],
                options={"verify_aud": False},
            )
            sub = payload.get("sub")
            if not sub:
                return None
            return {
                "sub": sub,
                "email": payload.get("email"),
                "is_anonymous": bool(payload.get("is_anonymous", False)),
            }
        except jwt.PyJWTError:
            continue
    return None


def _supabase_jwt_to_current_user(token: str) -> Optional[CurrentUser]:
    """Build a ``CurrentUser`` from a raw Supabase JWT.

    - Anonymous sessions (``is_anonymous`` or no email) map to role ``guest``.
    - Authenticated sessions default to role ``user``.
    - When the ``public.profiles`` table holds an explicit role, it overrides
      the default so an admin stored in profiles gets admin bypass behavior.
    """
    payload = verify_supabase_jwt(token)
    if not payload:
        return None

    if payload.get("is_anonymous") or not payload.get("email"):
        role = ROLE_GUEST
    else:
        role = ROLE_USER

    try:
        from app.services.supabase_service import supabase_service

        if supabase_service.is_enabled():
            profile = supabase_service.get_user_profile(payload["sub"])
            profile_role = (profile or {}).get("role")
            if profile_role in (ROLE_ADMIN, ROLE_USER, ROLE_GUEST):
                role = profile_role
    except Exception as exc:
        logger.exception("Failed to resolve profile role for %s: %s", payload["sub"], exc)

    return CurrentUser(
        sub=payload["sub"],
        role=role,
        email=payload.get("email") or None,
    )


_bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_to_user(credentials: Optional[HTTPAuthorizationCredentials]) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    # Preferred path: an app JWT issued by POST /api/auth/login.
    payload = decode_access_token(token)
    if payload:
        return CurrentUser(
            sub=payload["sub"],
            role=payload["role"],
            email=payload.get("email"),
        )

    # Fallback: a raw Supabase Auth JWT sent directly in the Authorization header.
    supabase_user = _supabase_jwt_to_current_user(token)
    if supabase_user:
        return supabase_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> CurrentUser:
    return _credentials_to_user(credentials)


def get_current_admin(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Like ``get_current_user`` but rejects non-admin callers with a 403."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
