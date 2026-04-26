"""
AIZEN Authentication Dependencies
===================================
FastAPI Security() dependency for Supabase JWT authentication.
Falls back to API Key if Supabase is disabled.
"""

import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Header scheme — clients send: Authorization: Bearer <JWT or API_KEY>
# ---------------------------------------------------------------------------
_api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def _extract_bearer(
    raw: str | None = Security(_api_key_header),
) -> str | None:
    """Strip the 'Bearer ' prefix if present."""
    if raw is None:
        return None
    if raw.startswith("Bearer "):
        return raw[7:]
    return raw


# ---------------------------------------------------------------------------
# Public dependency — returns authenticated user-id (or raises 401)
# ---------------------------------------------------------------------------
async def require_api_key(
    token: str | None = Depends(_extract_bearer),
) -> str:
    """
    Validate the Supabase JWT token or AIZEN API key.

    Returns the validated user_id.
    Raises 401 if missing or invalid.
    """
    settings = get_settings()
    server_key = getattr(settings, "aizen_api_key", "")
    client = get_supabase_client()

    # Supabase Verification
    if client:
        if token:
            try:
                user = client.auth.get_user(token)
                if user and user.user:
                    return user.user.id
            except Exception:
                pass  # Try other methods

    # Fallback to Server API Key
    if server_key and token == server_key:
        return "admin_user"

    # LOCAL DEV BYPASS: If no token and in dev mode, allow access
    if settings.environment != "production":
        logger.info("Local Development: Allowing anonymous access")
        return "dev-user"

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token.",
    )
