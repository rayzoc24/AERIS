"""Role-Based Access Control (security checks #4, #6)."""
from __future__ import annotations

from enum import Enum
from typing import Awaitable, Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security.jwt import TokenType, decode_token


class Role(str, Enum):
    ADMIN = "admin"
    DRIVER = "driver"
    CITIZEN = "citizen"


# auto_error=False so we can fall back to the access_token cookie when no
# Authorization header is present (e.g. after a page reload).
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """Extract and validate the current user from either the Authorization
    Bearer header or the HttpOnly access_token cookie.

    Priority: Bearer header > cookie.  Raises 401 if neither is present or
    if the token is invalid / expired.
    """
    token: Optional[str] = None

    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        # Fall back to the HttpOnly cookie set by /login and /register.
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token, expected_type=TokenType.ACCESS)
    request.state.user_id = payload["sub"]
    request.state.user_role = payload["role"]
    return payload


def require_roles(*allowed_roles: Role) -> Callable[..., Awaitable[dict]]:
    """Dependency that enforces one of the given roles for the route."""
    allowed = {r.value for r in allowed_roles}

    def _dependency(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _dependency


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    return require_roles(Role.ADMIN)(user)


def require_driver(user: dict = Depends(get_current_user)) -> dict:
    return require_roles(Role.DRIVER)(user)


def require_citizen(user: dict = Depends(get_current_user)) -> dict:
    return require_roles(Role.CITIZEN)(user)
