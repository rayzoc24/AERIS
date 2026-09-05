"""Vehicle models."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.common import GeoPoint


VEHICLE_TYPES = {"ambulance", "fire", "police", "rescue"}
VEHICLE_STATUSES = {"available", "dispatched", "en_route", "on_scene", "offline"}


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=3, max_length=20)
    type: str
    driver_id: Optional[str] = None

    @field_validator("type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        if v not in VEHICLE_TYPES:
            raise ValueError(f"Invalid vehicle type. Allowed: {sorted(VEHICLE_TYPES)}")
        return v

    @field_validator("registration_number")
    @classmethod
    def _normalize_reg(cls, v: str) -> str:
        return v.upper().strip()


class VehicleUpdate(BaseModel):
    status: Optional[str] = None
    driver_id: Optional[str] = None
    last_known_location: Optional[GeoPoint] = None

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v):
        if v is not None and v not in VEHICLE_STATUSES:
            raise ValueError(f"Invalid status. Allowed: {sorted(VEHICLE_STATUSES)}")
        return v


class VehicleOut(BaseModel):
    id: str
    registration_number: str
    type: str
    status: str
    driver_id: Optional[str]
    last_known_location: Optional[GeoPoint]
    current_trip_id: Optional[str]
    updated_at: datetime
