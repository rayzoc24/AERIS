"""Security package for AERIS backend.

Implements:
- JWT auth (security check #5)
- RBAC middleware (security check #6)
- Rate limiting (security check #11)
- CSP and security headers (security checks #8, #16)
- CSRF protection (security check #13)
- Input sanitisation (security check #7)
"""
from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenType,
)
from app.security.rbac import Role, require_roles, get_current_user, require_admin, require_driver, require_citizen
from app.security.rate_limit import limiter
from app.security.csrf import csrf_protect, validate_csrf_token
from app.security.sanitize import sanitize_string, sanitize_html

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "TokenType",
    "Role",
    "require_roles",
    "get_current_user",
    "require_admin",
    "require_driver",
    "require_citizen",
    "limiter",
    "csrf_protect",
    "validate_csrf_token",
    "sanitize_string",
    "sanitize_html",
]
