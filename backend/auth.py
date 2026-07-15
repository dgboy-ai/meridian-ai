"""JWT authentication middleware for FastAPI.

Requires: pip install python-jose[cryptography]
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from backend.config import settings

logger = logging.getLogger(__name__)

# Reusable bearer scheme (generates the Authorize button in /docs)
bearer_scheme = HTTPBearer(auto_error=False)


# ─── Token helpers ─────────────────────────────────────────────────────────────

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to encode (must include "sub" by convention).
        expires_delta: Custom expiry; defaults to AUTH_ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.auth.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.auth.secret_key, algorithm=settings.auth.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.auth.secret_key,
            algorithms=[settings.auth.algorithm],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ─── Dependency ────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """FastAPI dependency that extracts and validates the current user from Bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


# ─── Middleware ─────────────────────────────────────────────────────────────────

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that enforces JWT auth on every request.

    Controlled by AUTH_ENABLED env var. Public paths are always skipped.
    """

    def __init__(self, app: Any, public_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.public_paths = set(public_paths or settings.auth.public_paths)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Auth disabled globally — pass through
        if not settings.auth.enabled:
            return await call_next(request)

        # Always allow public / health / docs paths
        path = request.url.path
        if path in self.public_paths or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing or malformed Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[len("Bearer "):]
        try:
            payload = jwt.decode(
                token,
                settings.auth.secret_key,
                algorithms=[settings.auth.algorithm],
            )
        except JWTError as exc:
            logger.warning("JWT validation failed for %s: %s", path, exc)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": f"Invalid token: {exc}"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Attach decoded payload to request.state for downstream handlers
        request.state.user = payload
        return await call_next(request)
