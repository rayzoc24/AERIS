"""JWT generation and verification (security checks #5, #17)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status

from app.config import get_settings


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str, role: str, extra: Optional[Dict[str, Any]] = None) -> str:
    settings = get_settings()
    expire = _now() + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": TokenType.ACCESS.value,
        "exp": expire,
        "iat": _now(),
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, role: str) -> str:
    settings = get_settings()
    expire = _now() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": TokenType.REFRESH.value,
        "exp": expire,
        "iat": _now(),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: Optional[TokenType] = None) -> Dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if expected_type and payload.get("type") != expected_type.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
    return payload
