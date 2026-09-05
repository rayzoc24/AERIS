"""Authentication routes (security checks #5, #11, #17).

Login issues access + refresh tokens. Access token is returned in the
response body for short-lived use; both tokens are also stored in
HttpOnly, Secure, SameSite=Strict cookies. A CSRF token is issued and
stored in a non-HttpOnly cookie so the frontend can echo it back.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from bson import ObjectId

from app.database import get_db
from app.config import get_settings
from app.models.user import UserCreate, UserLogin, TokenBundle, UserOut
from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenType,
)
from app.security.rbac import Role, get_current_user
from app.security.csrf import issue_csrf_token
from app.security.rate_limit import limiter
from app.security.middleware import set_auth_cookie, clear_auth_cookie

logger = logging.getLogger("aeris.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

_pwd = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return _pwd.hash(password)


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return _pwd.verify(password, hashed)
    except Exception:
        return False


@router.post("/register", response_model=TokenBundle, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(payload: UserCreate, request: Request, response: Response) -> TokenBundle:
    db = get_db()
    settings = get_settings()

    # Prevent self-registration of admin accounts.
    if payload.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin accounts cannot self-register")

    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    now = datetime.now(timezone.utc)
    doc = {
        "email": payload.email.lower(),
        "name": payload.name,
        "role": payload.role,
        "password_hash": _hash_password(payload.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)

    bundle = _issue_tokens(user_id, payload.role, UserOut(
        id=user_id,
        email=payload.email,
        name=payload.name,
        role=payload.role,
        is_active=True,
        created_at=now,
        updated_at=now,
    ), settings)

    # Set the same HttpOnly auth cookies that /login sets so the user is
    # immediately authenticated without a second round-trip.
    set_auth_cookie(response, "access_token", bundle.access_token, settings.JWT_ACCESS_EXPIRE_MINUTES * 60)
    set_auth_cookie(response, "refresh_token", bundle.refresh_token, settings.JWT_REFRESH_EXPIRE_DAYS * 86400)
    # csrf_token must be non-HttpOnly so the JS interceptor can read it.
    response.set_cookie(
        key="csrf_token",
        value=bundle.csrf_token,
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        httponly=False,
        secure=settings.SECURE_COOKIES,
        samesite="strict",
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    return bundle


@router.post("/login", response_model=TokenBundle)
@limiter.limit("10/minute")
async def login(payload: UserLogin, request: Request, response: Response) -> TokenBundle:
    db = get_db()
    settings = get_settings()
    user_doc = await db.users.find_one({"email": payload.email.lower()})
    if not user_doc or not user_doc.get("is_active") or not _verify_password(payload.password, user_doc["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_id = str(user_doc["_id"])
    user_out = UserOut(
        id=user_id,
        email=user_doc["email"],
        name=user_doc["name"],
        role=user_doc["role"],
        is_active=user_doc["is_active"],
        created_at=user_doc["created_at"],
        updated_at=user_doc["updated_at"],
    )
    bundle = _issue_tokens(user_id, user_doc["role"], user_out, settings)
    set_auth_cookie(response, "access_token", bundle.access_token, settings.JWT_ACCESS_EXPIRE_MINUTES * 60)
    set_auth_cookie(response, "refresh_token", bundle.refresh_token, settings.JWT_REFRESH_EXPIRE_DAYS * 86400)
    return bundle


@router.post("/refresh", response_model=TokenBundle)
@limiter.limit("20/minute")
async def refresh(request: Request) -> TokenBundle:
    settings = get_settings()
    refresh_cookie = request.cookies.get("refresh_token")
    if not refresh_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    payload = decode_token(refresh_cookie, expected_type=TokenType.REFRESH)
    db = get_db()
    user_doc = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user_doc or not user_doc.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    user_out = UserOut(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        name=user_doc["name"],
        role=user_doc["role"],
        is_active=user_doc["is_active"],
        created_at=user_doc["created_at"],
        updated_at=user_doc["updated_at"],
    )
    return _issue_tokens(str(user_doc["_id"]), user_doc["role"], user_out, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> Response:
    clear_auth_cookie(response, "access_token")
    clear_auth_cookie(response, "refresh_token")
    clear_auth_cookie(response, "csrf_token")
    return response


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)) -> UserOut:
    """Return the currently authenticated user's profile."""
    db = get_db()
    user_doc = await db.users.find_one({"_id": ObjectId(user["sub"])})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        name=user_doc["name"],
        role=user_doc["role"],
        is_active=user_doc["is_active"],
        created_at=user_doc["created_at"],
        updated_at=user_doc["updated_at"],
    )


def _issue_tokens(user_id: str, role: str, user: UserOut, settings) -> TokenBundle:
    access = create_access_token(user_id, role)
    refresh = create_refresh_token(user_id, role)
    csrf = issue_csrf_token()
    return TokenBundle(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        csrf_token=csrf,
        user=user,
    )
