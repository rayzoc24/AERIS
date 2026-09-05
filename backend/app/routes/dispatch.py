"""Dispatch & trip management routes."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.database import get_db
from app.models.trip import TripCreate, TripOut, TripStatusUpdate, GreenCorridorUpdate
from app.models.vehicle import VehicleOut
from app.models.common import PaginatedResponse
from app.security.rbac import require_roles, Role, get_current_user

logger = logging.getLogger("aeris.dispatch")
router = APIRouter(prefix="/dispatch", tags=["dispatch"])


def _serialize_trip(doc) -> TripOut:
    return TripOut(
        id=str(doc["_id"]),
        vehicle_id=str(doc["vehicle_id"]),
        driver_id=str(doc["driver_id"]) if doc.get("driver_id") else None,
        status=doc["status"],
        priority=doc.get("priority", "high"),
        origin=doc["origin"],
        destination=doc["destination"],
        route_polyline=doc.get("route_polyline"),
        green_corridor=doc.get("green_corridor"),
        started_at=doc["started_at"],
        ended_at=doc.get("ended_at"),
        eta_seconds=doc.get("eta_seconds"),
        distance_metres=doc.get("distance_metres"),
    )


@router.get("/trips", response_model=PaginatedResponse[TripOut])
async def list_trips(
    request: Request,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
) -> PaginatedResponse[TripOut]:
    db = get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter
    total = await db.trips.count_documents(query)
    cursor = db.trips.find(query).sort("started_at", -1).skip((page - 1) * page_size).limit(page_size)
    items = [_serialize_trip(doc) async for doc in cursor]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/trips", response_model=TripOut, status_code=status.HTTP_201_CREATED)
async def create_trip(
    payload: TripCreate,
    request: Request,
    user: dict = Depends(require_roles(Role.ADMIN, Role.DRIVER)),
) -> TripOut:
    db = get_db()
    vehicle_doc = await db.vehicles.find_one({"_id": ObjectId(payload.vehicle_id)})
    if not vehicle_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    if vehicle_doc["status"] != "available":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle not available")

    now = datetime.now(timezone.utc)
    doc = {
        "vehicle_id": ObjectId(payload.vehicle_id),
        "driver_id": ObjectId(vehicle_doc["driver_id"]) if vehicle_doc.get("driver_id") else None,
        "status": "active",
        "priority": payload.priority,
        "origin": payload.origin.model_dump(),
        "destination": payload.destination.model_dump(),
        "route_polyline": None,
        "green_corridor": None,
        "started_at": now,
        "ended_at": None,
    }
    result = await db.trips.insert_one(doc)
    await db.vehicles.update_one(
        {"_id": ObjectId(payload.vehicle_id)},
        {"$set": {"status": "dispatched", "current_trip_id": result.inserted_id, "updated_at": now}},
    )
    doc["_id"] = result.inserted_id
    return _serialize_trip(doc)


@router.get("/trips/{trip_id}", response_model=TripOut)
async def get_trip(trip_id: str, request: Request, user: dict = Depends(get_current_user)) -> TripOut:
    db = get_db()
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trip id")
    doc = await db.trips.find_one({"_id": ObjectId(trip_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return _serialize_trip(doc)


@router.patch("/trips/{trip_id}/status", response_model=TripOut)
async def update_trip_status(
    trip_id: str,
    payload: TripStatusUpdate,
    request: Request,
    user: dict = Depends(require_roles(Role.ADMIN, Role.DRIVER)),
) -> TripOut:
    db = get_db()
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trip id")
    update = {"status": payload.status}
    if payload.status == "completed":
        update["ended_at"] = datetime.now(timezone.utc)
    result = await db.trips.find_one_and_update(
        {"_id": ObjectId(trip_id)},
        {"$set": update},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return _serialize_trip(result)


@router.put("/trips/{trip_id}/green-corridor", response_model=TripOut)
async def set_green_corridor(
    trip_id: str,
    payload: GreenCorridorUpdate,
    request: Request,
    user: dict = Depends(require_roles(Role.ADMIN)),
) -> TripOut:
    db = get_db()
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trip id")
    result = await db.trips.find_one_and_update(
        {"_id": ObjectId(trip_id)},
        {"$set": {"green_corridor": payload.signal_sequence, "route_polyline": payload.corridor_polyline}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return _serialize_trip(result)


@router.get("/vehicles", response_model=List[VehicleOut])
async def list_vehicles(
    request: Request,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
) -> List[VehicleOut]:
    db = get_db()
    query = {"status": status_filter} if status_filter else {}
    docs = await db.vehicles.find(query).to_list(length=200)
    return [
        VehicleOut(
            id=str(doc["_id"]),
            registration_number=doc["registration_number"],
            type=doc["type"],
            status=doc["status"],
            driver_id=str(doc["driver_id"]) if doc.get("driver_id") else None,
            last_known_location=doc.get("last_known_location"),
            current_trip_id=str(doc["current_trip_id"]) if doc.get("current_trip_id") else None,
            updated_at=doc.get("updated_at", doc.get("created_at")),
        )
        async for doc in db.vehicles.find(query)
    ]
