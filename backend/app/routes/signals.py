"""Signal preemption and watchdog routes (feature #1)."""
import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.database import get_db
from app.models.signal import SignalPreemptionCreate, SignalPreemptionOut, SignalWatchdogUpdate
from app.security.rbac import require_roles, Role, get_current_user

logger = logging.getLogger("aeris.signals")
router = APIRouter(prefix="/signals", tags=["signals"])


def _serialize(doc) -> SignalPreemptionOut:
    return SignalPreemptionOut(
        id=str(doc["_id"]),
        trip_id=str(doc["trip_id"]),
        signal_id=doc["signal_id"],
        state=doc["state"],
        triggered_at=doc["triggered_at"],
        reverted_at=doc.get("reverted_at"),
        watchdog_active=doc.get("watchdog_active", False),
    )


@router.post("/preempt", response_model=SignalPreemptionOut, status_code=status.HTTP_201_CREATED)
async def preempt_signal(
    payload: SignalPreemptionCreate,
    request: Request,
    user: dict = Depends(require_roles(Role.ADMIN)),
) -> SignalPreemptionOut:
    db = get_db()
    if not ObjectId.is_valid(payload.trip_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trip id")
    doc = {
        "trip_id": ObjectId(payload.trip_id),
        "signal_id": payload.signal_id,
        "state": payload.target_state,
        "triggered_at": datetime.now(timezone.utc),
        "reverted_at": None,
        "watchdog_active": False,
    }
    result = await db.signal_preemptions.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Signal %s preemption to %s for trip %s by %s",
                payload.signal_id, payload.target_state, payload.trip_id, user["sub"])
    return _serialize(doc)


@router.post("/watchdog", response_model=SignalPreemptionOut)
async def watchdog_revert(
    payload: SignalWatchdogUpdate,
    request: Request,
    user: dict = Depends(require_roles(Role.ADMIN)),
) -> SignalPreemptionOut:
    """Revert the most recent preemption for the given signal (GPS lost, etc.)."""
    db = get_db()
    doc = await db.signal_preemptions.find_one_and_update(
        {"signal_id": payload.signal_id, "reverted_at": None, "state": {"$ne": "reverted"}},
        {
            "$set": {
                "state": "reverted",
                "reverted_at": datetime.now(timezone.utc),
                "watchdog_active": True,
                "watchdog_reason": payload.reason,
            }
        },
        return_document=True,
        sort=[("triggered_at", -1)],
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active preemption not found for signal")
    logger.warning("Watchdog revert on signal %s reason=%s forced=%s by %s",
                   payload.signal_id, payload.reason, payload.force_revert, user["sub"])
    return _serialize(doc)


@router.get("/active", response_model=list[SignalPreemptionOut])
async def list_active_preemptions(
    request: Request,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    cursor = db.signal_preemptions.find({"reverted_at": None})
    return [_serialize(doc) async for doc in cursor]


@router.get("/history/{trip_id}", response_model=list[SignalPreemptionOut])
async def list_trip_preemptions(
    trip_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trip id")
    db = get_db()
    cursor = db.signal_preemptions.find({"trip_id": ObjectId(trip_id)}).sort("triggered_at", 1)
    return [_serialize(doc) async for doc in cursor]
