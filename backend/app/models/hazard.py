"""Citizen hazard report models."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.common import GeoPoint

HAZARD_TYPES = {"accident", "pothole", "flooding", "obstruction", "road_work", "vehicle_breakdown"}
HAZARD_SEVERITIES = {"low", "medium", "high", "critical"}
HAZARD_STATUSES = {"active", "verified", "resolved", "dismissed"}


class HazardCreate(BaseModel):
    type: str
    severity: str = "medium"
    location: GeoPoint
    description: str = Field(default="", max_length=1000)
    nearest_landmark: Optional[str] = Field(default=None, max_length=200)
    image_ids: List[str] = Field(default_factory=list, max_length=4)

    @field_validator("type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        if v not in HAZARD_TYPES:
            raise ValueError(f"Invalid hazard type. Allowed: {sorted(HAZARD_TYPES)}")
        return v

    @field_validator("severity")
    @classmethod
    def _validate_severity(cls, v: str) -> str:
        if v not in HAZARD_SEVERITIES:
            raise ValueError(f"Invalid severity. Allowed: {sorted(HAZARD_SEVERITIES)}")
        return v


class HazardCorroborate(BaseModel):
    """A citizen confirmation that a hazard is still present."""
    same_location: bool = True
    note: Optional[str] = Field(default=None, max_length=200)


class HazardOut(BaseModel):
    id: str
    type: str
    severity: str
    status: str
    location: GeoPoint
    description: str
    reported_by: str
    corroboration_score: float
    image_urls: List[str]
    created_at: datetime
    updated_at: datetime
