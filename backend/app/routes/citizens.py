"""Citizen-facing endpoints (reporting, alerts, account)."""
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.config import get_settings
from app.database import get_db
from app.models.hazard import HazardOut
from app.security.rate_limit import limiter
from app.security.rbac import get_current_user, require_roles, Role

logger = logging.getLogger("aeris.citizens")
router = APIRouter(prefix="/citizens", tags=["citizens"])


@router.post("/reports/uploads")
@limiter.limit("10/minute")
async def upload_report_image(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(require_roles(Role.CITIZEN, Role.ADMIN, Role.DRIVER)),
):
    """Secure file upload (security check #12)."""
    settings = get_settings()
    if file.content_type not in settings.ALLOWED_UPLOAD_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported MIME type: {file.content_type}",
        )

    bytes_read = 0
    chunks = []
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        bytes_read += len(chunk)
        if bytes_read > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_BYTES} bytes",
            )
        if b"\x00script" in chunk.lower() or b"<!doctype" in chunk.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content failed validation",
            )
        chunks.append(chunk)

    upload_id = str(uuid.uuid4())
    upload_dir = Path("/home/z/my-project/aeris/backend/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if safe_ext not in {"jpg", "jpeg", "png", "webp"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file extension")
    target = upload_dir / f"{upload_id}.{safe_ext}"
    with open(target, "wb") as f:
        for chunk in chunks:
            f.write(chunk)
    logger.info("Upload %s by %s type=%s size=%d", upload_id, user["sub"], file.content_type, bytes_read)
    return {"image_id": upload_id, "size_bytes": bytes_read, "mime_type": file.content_type}


@router.get("/me/reports", response_model=List[HazardOut])
async def my_reports(
    request: Request,
    user: dict = Depends(require_roles(Role.CITIZEN, Role.DRIVER)),
):
    db = get_db()
    cursor = db.hazards.find({"reported_by": ObjectId(user["sub"])}).sort("created_at", -1)
    from app.routes.hazards import _serialize
    return [_serialize(doc) async for doc in cursor]

