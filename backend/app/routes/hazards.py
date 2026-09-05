"""Hazard & accident reporting routes (features #3, #4)."""
import logging
import math
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.database import get_db
from app.models.hazard import HazardCreate, HazardCorroborate, HazardOut
from app.models.common import PaginatedResponse, BoundingBox
from app.security.rate_limit import limiter
from app.security.rbac import get_current_user, require_roles, Role

logger = logging.getLogger("aeris.hazards")
router = APIRouter(prefix="/hazards", tags=["hazards"])


HAZARD_SEVERITY_WEIGHT = {"low": 0.2, "medium": 0.5, "high": 0.75, "critical": 1.0}


def _serialize(doc) -> HazardOut:
    return HazardOut(
        id=str(doc["_id"]),
        type=doc["type"],
        severity=doc["severity"],
        status=doc.get("status", "active"),
        location=doc["location"],
        description=doc.get("description", ""),
        reported_by=str(doc["reported_by"]),
        corroboration_score=float(doc.get("corroboration_score", 0.0)),
        image_urls=doc.get("image_urls", []),
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at", doc["created_at"]),
    )


@router.get("", response_model=PaginatedResponse[HazardOut])
async def list_hazards(
    request: Request,
    type_filter: Optional[str] = Query(default=None, alias="type"),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    bbox: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
) -> PaginatedResponse[HazardOut]:
    db = get_db()
    query = {}
    if type_filter:
        query["type"] = type_filter
    if status_filter:
        query["status"] = status_filter
    if bbox:
        try:
            parts = [float(x) for x in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            south, west, north, east = parts
            query["location"] = {
                "$geoWithin": {
                    "$box": [[west, south], [east, north]],
                }
            }
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bbox format")

    total = await db.hazards.count_documents(query)
    cursor = db.hazards.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    items = [_serialize(doc) async for doc in cursor]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{hazard_id}", response_model=HazardOut)
async def get_hazard(hazard_id: str, request: Request, user: dict = Depends(get_current_user)) -> HazardOut:
    db = get_db()
    if not ObjectId.is_valid(hazard_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
    doc = await db.hazards.find_one({"_id": ObjectId(hazard_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hazard not found")
    return _serialize(doc)


@router.post("", response_model=HazardOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_hazard(
    payload: HazardCreate,
    request: Request,
    user: dict = Depends(get_current_user),
) -> HazardOut:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        "type": payload.type,
        "severity": payload.severity,
        "status": "active",
        "location": payload.location.model_dump(),
        "description": payload.description,
        "nearest_landmark": payload.nearest_landmark,
        "image_ids": payload.image_ids,
        "image_urls": [],
        "reported_by": ObjectId(user["sub"]),
        "corroboration_score": 0.0,
        "corroborations": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db.hazards.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Hazard %s reported by %s", payload.type, user["sub"])
    return _serialize(doc)


@router.post("/{hazard_id}/corroborate", response_model=HazardOut)
@limiter.limit("30/minute")
async def corroborate_hazard(
    hazard_id: str,
    payload: HazardCorroborate,
    request: Request,
    user: dict = Depends(get_current_user),
) -> HazardOut:
    """A citizen confirms the hazard is still present. Raises corroboration score."""
    db = get_db()
    if not ObjectId.is_valid(hazard_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
    existing = await db.hazards.find_one({"_id": ObjectId(hazard_id)})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hazard not found")
    if existing.get("status") in {"resolved", "dismissed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hazard is no longer active")

    corroborations = existing.get("corroborations", [])
    if any(str(c.get("user_id")) == user["sub"] for c in corroborations):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already corroborated this hazard")

    corroborations.append({
        "user_id": ObjectId(user["sub"]),
        "note": payload.note,
        "at": datetime.now(timezone.utc),
    })
    base = HAZARD_SEVERITY_WEIGHT.get(existing["severity"], 0.5)
    # Logistic-style growth capped at 1.0 to avoid runaway weighting.
    score = round(min(1.0, base + (1 - base) * (1 - math.exp(-0.3 * len(corroborations)))), 4)

    updated = await db.hazards.find_one_and_update(
        {"_id": ObjectId(hazard_id)},
        {
            "$set": {
                "corroborations": corroborations,
                "corroboration_score": score,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=True,
    )
    return _serialize(updated)


@router.patch("/{hazard_id}/status", response_model=HazardOut)
async def update_hazard_status(
    hazard_id: str,
    new_status: str,
    request: Request,
    user: dict = Depends(require_roles(Role.ADMIN)),
) -> HazardOut:
    db = get_db()
    if new_status not in {"active", "verified", "resolved", "dismissed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    if not ObjectId.is_valid(hazard_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
    doc = await db.hazards.find_one_and_update(
        {"_id": ObjectId(hazard_id)},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hazard not found")
    return _serialize(doc)
