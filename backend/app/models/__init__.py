"""AERIS API request/response models (security check #7 - input validation).

Every wire payload that crosses the API boundary is bound to a Pydantic
model so FastAPI rejects malformed or oversized input before it reaches
business logic.
"""
from app.models.user import (
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
    TokenBundle,
)
from app.models.vehicle import VehicleCreate, VehicleUpdate, VehicleOut
from app.models.trip import (
    TripCreate,
    TripOut,
    TripStatusUpdate,
    GreenCorridorUpdate,
)
from app.models.signal import (
    SignalPreemptionCreate,
    SignalPreemptionOut,
    SignalWatchdogUpdate,
)
from app.models.hazard import (
    HazardCreate,
    HazardOut,
    HazardCorroborate,
)
from app.models.road_segment import (
    RoadSegmentCreate,
    RoadSegmentOut,
    RiskScoreUpdate,
)
from app.models.common import (
    GeoPoint,
    BoundingBox,
    PaginatedResponse,
    ErrorResponse,
    HealthStatus,
)

__all__ = [
    "UserCreate", "UserLogin", "UserOut", "UserUpdate", "TokenBundle",
    "VehicleCreate", "VehicleUpdate", "VehicleOut",
    "TripCreate", "TripOut", "TripStatusUpdate", "GreenCorridorUpdate",
    "SignalPreemptionCreate", "SignalPreemptionOut", "SignalWatchdogUpdate",
    "HazardCreate", "HazardOut", "HazardCorroborate",
    "RoadSegmentCreate", "RoadSegmentOut", "RiskScoreUpdate",
    "GeoPoint", "BoundingBox", "PaginatedResponse", "ErrorResponse", "HealthStatus",
]
