"""AERIS backend entrypoint.

Implements the 19 security checks from context.md:
 1. Hide API keys -> keys live in .env, loaded via Settings
 2. Check env vars -> Settings validates required vars at startup
 3. .gitignore -> provided separately, .env never committed
 4. Protect admin routes -> require_roles(Role.ADMIN) dependency
 5. Add auth -> JWT access + refresh tokens
 6. RBAC -> Role enum + require_roles(...) dependency
 7. Sanitize inputs -> Pydantic models + sanitize_string/sanitize_html
 8. XSS / CSP -> SecurityHeadersMiddleware with strict CSP
 9. NoSQL injection -> Motor with parameterised queries + JSON schema validators
10. DB rules -> COLLECTION_VALIDATORS in database.py (strict)
11. Rate limiting -> SlowAPI + Redis
12. Secure file uploads -> MIME + size + content sniff checks
13. CSRF -> csrf_token cookie + X-CSRF-Token header validation
14. CORS -> strict allowlist from CORS_ALLOWED_ORIGINS env var
15. HSTS -> Strict-Transport-Security header in production
16. Security headers -> SecurityHeadersMiddleware
17. Secure cookies -> HttpOnly, Secure, SameSite=Strict
18. Disable debug -> uvicorn run uses reload=False, DEBUG=False in prod
19. Prod settings -> ENABLE_SWAGGER=False in prod, multi-worker, logging config
"""
from __future__ import annotations

import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import close_db, init_db
from app.routes import ROUTERS
from app.security.middleware import SecurityHeadersMiddleware
from app.security.rate_limit import setup_rate_limiting
from app.services.firebase import firebase_client
from app.services.mappls import mappls_client


def _configure_logging() -> None:
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {"level": "WARNING"},
            "uvicorn.access": {"level": "WARNING"},
        },
    })


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    logger = logging.getLogger("aeris")
    logger.info("Starting AERIS backend, env=%s", settings.APP_ENV)
    await init_db()
    yield
    logger.info("Shutting down AERIS backend")
    await close_db()
    await mappls_client.close()
    await firebase_client.close()


settings = get_settings()
app = FastAPI(
    title="AERIS API",
    description="Autonomous Emergency Response & Green Corridor System",
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.ENABLE_SWAGGER else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.ENABLE_SWAGGER else None,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


# --- Middleware ---------------------------------------------------------------
setup_rate_limiting(app)

# Strict CORS (security check #14) - never use ["*"].
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

# Security headers + CSP (security check #8, #16).
app.add_middleware(SecurityHeadersMiddleware, report_only_csp=False)

# HTTPS redirect + HSTS in production (security check #15).
if settings.APP_ENV == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    allowed_host = settings.PUBLIC_BASE_URL.replace("https://", "").replace("http://", "").split("/")[0]
    if ":" in allowed_host:
        allowed_host = allowed_host.split(":")[0]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[allowed_host] if allowed_host else ["*"])


# --- Routes -------------------------------------------------------------------
for name, router in ROUTERS:
    app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid as _uuid
    request.state.request_id = str(_uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.get("/")
async def root(request: Request):
    return JSONResponse({
        "name": "AERIS API",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/api/docs" if settings.ENABLE_SWAGGER else None,
    })


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger("aeris")
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please slow down.",
            "code": "RATE_LIMIT",
            "request_id": getattr(request.state, "request_id", None),
        },
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )


if __name__ == "__main__":
    import uvicorn

    workers = 1 if settings.APP_ENV != "production" else 4
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        workers=workers,
        log_level="info",
        access_log=settings.DEBUG,
        use_colors=False,
    )
