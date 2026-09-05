"""CSRF token issuance and validation (security check #13).

The frontend reads the token from the X-CSRF-Token cookie after a
successful login and resends it in the X-CSRF-Token header on every
state-changing request. The token is HMAC-signed.
"""
from __future__ import annotations

import hmac
import secrets
from typing import Optional

from fastapi import Cookie, HTTPException, Header, Request, status

from app.config import get_settings


def issue_csrf_token() -> str:
    settings = get_settings()
    raw = secrets.token_urlsafe(32)
    sig = hmac.new(settings.CSRF_SECRET.encode(), raw.encode(), digestmod="sha256").hexdigest()
    return f"{raw}.{sig}"


def _verify_csrf_token(token: str) -> bool:
    settings = get_settings()
    if not token or "." not in token:
        return False
    raw, sig = token.rsplit(".", 1)
    expected_sig = hmac.new(settings.CSRF_SECRET.encode(), raw.encode(), digestmod="sha256").hexdigest()
    return hmac.compare_digest(sig, expected_sig)


async def validate_csrf_token(
    request: Request,
    x_csrf_token: Optional[str] = Header(default=None, alias="X-CSRF-Token"),
    csrf_cookie: Optional[str] = Cookie(default=None, alias="csrf_token"),
) -> None:
    """Dependency: state-changing methods must pass a valid CSRF token."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if not x_csrf_token or not csrf_cookie or not _verify_csrf_token(x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token",
        )
    if not hmac.compare_digest(x_csrf_token, csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch",
        )


async def csrf_protect(request: Request) -> None:
    """Helper to apply CSRF check inside routes that bypass auto-deps."""
    await validate_csrf_token(
        request,
        request.headers.get("X-CSRF-Token"),
        request.cookies.get("csrf_token"),
    )
