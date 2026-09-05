"""Trip and dispatch models."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.common import GeoPoint

TRIP_STATUSES = {"pending", "active", "completed", "cancelled"}
TRIP_PRIORITIES = {"low", "standard", "high", "critical"}


class TripCreate(BaseModel):
    vehicle_id: str
    origin: GeoPoint
    destination: GeoPoint
    priority: str = "high"
    caller_name: Optional[str] = Field(default=None, max_length=120)
    caller_phone: Optional[str] = Field(default=None, max_length=20)
    incident_type: Optional[str] = Field(default=None, max_length=60)

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, v: str) -> str:
        if v not in TRIP_PRIORITIES:
            raise ValueError(f"Invalid priority. Allowed: {sorted(TRIP_PRIORITIES)}")
        return v

    @field_validator("caller_phone")
    @classmethod
    def _strip_phone(cls, v):
        if v is None:
            return None
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if len(cleaned) < 7 or len(cleaned) > 16:
            raise ValueError("Phone number length invalid")
        return cleaned


class TripStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        if v not in TRIP_STATUSES:
            raise ValueError(f"Invalid trip status. Allowed: {sorted(TRIP_STATUSES)}")
        return v


class GreenCorridorUpdate(BaseModel):
    signal_sequence: List[str] = Field(min_length=1)
    corridor_polyline: Optional[str] = None


class TripOut(BaseModel):
    id: str
    vehicle_id: str
    driver_id: Optional[str]
    status: str
    priority: str
    origin: GeoPoint
    destination: GeoPoint
    route_polyline: Optional[str]
    green_corridor: Optional[List[str]]
    started_at: datetime
    ended_at: Optional[datetime]
    eta_seconds: Optional[int] = None
    distance_metres: Optional[int] = None
