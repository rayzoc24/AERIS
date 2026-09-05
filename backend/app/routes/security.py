"""Security reporting endpoints (CSP report endpoint, CSRF token refresh)."""
import logging

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.security.csrf import issue_csrf_token
from app.security.middleware import set_auth_cookie
from app.security.rbac import get_current_user

router = APIRouter(prefix="/security", tags=["security"])
logger = logging.getLogger("aeris.security")


@router.post("/csp-report")
async def csp_report(request: Request) -> JSONResponse:
    """Receive Content Security Policy violation reports."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=204, content=None)
    report = body.get("csp-report", {})
    logger.warning(
        "CSP violation: document-uri=%s blocked-uri=%s directive=%s",
        report.get("document-uri"),
        report.get("blocked-uri"),
        report.get("violated-directive"),
    )
    return JSONResponse(status_code=204, content=None)


@router.get("/csrf-token")
async def refresh_csrf_token(user: dict = Depends(get_current_user)) -> Response:
    """Issue a fresh CSRF token after authentication."""
    token = issue_csrf_token()
    response = JSONResponse({"csrf_token": token})
    set_auth_cookie(response, "csrf_token", token, max_age=60 * 60 * 24)
    return response
