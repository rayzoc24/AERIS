"""Security middleware bundle (security checks #8, #15, #16, #17).

- Strict Content-Security-Policy that disables inline scripts/styles
  except for nonces that we inject per-request.
- HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
  Permissions-Policy, Cross-Origin headers.
- Cookie hardening (HttpOnly, Secure, SameSite=Strict) for auth cookies.
"""
from __future__ import annotations

import secrets
from typing import Iterable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


def _build_csp_header(report_only: bool = False) -> str:
    settings = get_settings()
    report_endpoint = f"{settings.BACKEND_BASE_URL}/api/v1/security/csp-report"
    header = (
        "default-src 'self';"
        "script-src 'self' 'nonce-{nonce}' 'strict-dynamic';"
        "style-src 'self' 'nonce-{nonce}';"
        "img-src 'self' data: https://apis.mappls.com;"
        "font-src 'self';"
        "connect-src 'self' https://apis.mappls.com wss: ws:;"
        "frame-ancestors 'none';"
        "form-action 'self';"
        "base-uri 'self';"
        "object-src 'none';"
        f"report-uri {report_endpoint};"
    )
    name = "Content-Security-Policy-Report-Only" if report_only else "Content-Security-Policy"
    return name, header


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers and CSP to every response."""

    def __init__(self, app, report_only_csp: bool = False):
        super().__init__(app)
        self.report_only = report_only_csp

    async def dispatch(self, request: Request, call_next):
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response: Response = await call_next(request)
        settings = get_settings()

        csp_name, csp_template = _build_csp_header(self.report_only)
        response.headers[csp_name] = csp_template.format(nonce=nonce)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(self), microphone=(), camera=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        if settings.APP_ENV == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
            response.headers.setdefault("Cache-Control", "no-store")
            response.headers.pop("Server", None)

        response.headers.setdefault("X-Request-ID", getattr(request.state, "request_id", ""))
        return response


def set_auth_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    """Set hardened cookies for auth tokens (security check #17)."""
    settings = get_settings()
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="strict",
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )


def clear_auth_cookie(response: Response, key: str) -> None:
    response.delete_cookie(key=key, path="/", domain=get_settings().COOKIE_DOMAIN)
