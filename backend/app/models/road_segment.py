"""Road segment and ML risk score models."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoadSegmentCreate(BaseModel):
    segment_id: str = Field(min_length=1, max_length=64)
    geometry: Dict  # GeoJSON LineString
    road_name: Optional[str] = Field(default=None, max_length=200)
    blackspot: bool = False

    @field_validator("geometry")
    @classmethod
    def _validate_geometry(cls, v):
        if not isinstance(v, dict) or v.get("type") not in {"LineString", "MultiLineString"}:
            raise ValueError("geometry must be GeoJSON LineString or MultiLineString")
        coords = v.get("coordinates")
        if not coords or not isinstance(coords, list):
            raise ValueError("coordinates missing")
        return v


class RiskScoreUpdate(BaseModel):
    # Pydantic v2 protects fields starting with "model_". Disable that
    # protection because "model_version" is a legitimate field name here.
    model_config = ConfigDict(protected_namespaces=())

    risk_score: float = Field(ge=0, le=1)
    risk_factors: Optional[Dict[str, float]] = None
    model_version: Optional[str] = Field(default=None, max_length=40)


class RoadSegmentOut(BaseModel):
    id: str
    segment_id: str
    geometry: Dict
    road_name: Optional[str]
    risk_score: float
    risk_factors: Dict[str, float]
    blackspot: bool
    last_updated: datetime
