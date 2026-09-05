"""Rate limiting using SlowAPI + Redis (security check #11)."""
from __future__ import annotations

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import get_settings


def _key_builder(client_ip: str = "") -> str:
    """Default key builder used by SlowAPI. We override only when auth context exists."""
    return client_ip


settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    strategy="fixed-window",
)


def setup_rate_limiting(app) -> None:
    """Attach SlowAPI state, exception handler, and middleware to the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(429, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


async def _rate_limit_exceeded_handler(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )
