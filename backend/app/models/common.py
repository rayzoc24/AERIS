"""Common shared models: geo, pagination, error, health."""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class GeoPoint(BaseModel):
    type: str = Field(default="Point", pattern="^Point$")
    coordinates: List[float] = Field(min_length=2, max_length=2)

    @field_validator("coordinates")
    @classmethod
    def _validate_coords(cls, v):
        lon, lat = v
        if not -180 <= lon <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        if not -90 <= lat <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return [float(lon), float(lat)]


class BoundingBox(BaseModel):
    """Bounding box for spatial queries."""
    south: float = Field(ge=-90, le=90)
    west: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    request_id: Optional[str] = None


class HealthStatus(BaseModel):
    status: str
    version: str
    services: dict
    timestamp: str
