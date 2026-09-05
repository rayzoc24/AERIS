"""Health and readiness endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.config import get_settings
from app.database import get_db
from app.models.common import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health_check(request: Request) -> HealthStatus:
    settings = get_settings()
    services = {"database": "ok", "mappls": "ok", "redis": "ok"}
    try:
        await get_db().command("ping")
    except Exception:
        services["database"] = "error"
    return HealthStatus(
        status="ok" if all(v == "ok" for v in services.values()) else "degraded",
        version=settings.APP_VERSION,
        services=services,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=HealthStatus)
async def readiness_check(request: Request) -> HealthStatus:
    return await health_check(request)
