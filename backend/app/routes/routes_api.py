"""Routing endpoints (Mappls wrappers, ML risk analysis)."""
import logging
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.database import get_db
from app.models.common import BoundingBox, GeoPoint
from app.security.rbac import get_current_user
from app.services.mappls import mappls_client
from app.services.ml_engine import risk_engine

logger = logging.getLogger("aeris.routes")
router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/route")
async def get_route(
    request: Request,
    origin_lon: float = Query(..., ge=-180, le=180),
    origin_lat: float = Query(..., ge=-90, le=90),
    dest_lon: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    avoid: Optional[List[str]] = Query(default=None),
    user: dict = Depends(get_current_user),
):
    try:
        data = await mappls_client.get_route((origin_lon, origin_lat), (dest_lon, dest_lat), avoid=avoid)
    except Exception as exc:
        logger.error("Mappls route error: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Routing provider unavailable")
    return data


@router.get("/traffic")
async def get_traffic(
    request: Request,
    bbox: str = Query(..., description="south,west,north,east"),
    user: dict = Depends(get_current_user),
):
    try:
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must have 4 values")
        data = await mappls_client.get_traffic((parts[0], parts[1], parts[2], parts[3]))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Mappls traffic error: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Traffic provider unavailable")
    return data


@router.get("/geocode")
async def geocode_address(
    request: Request,
    q: str = Query(..., min_length=2, max_length=200),
    user: dict = Depends(get_current_user),
):
    result = await mappls_client.geocode(q)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not resolved")
    return {"longitude": result[0], "latitude": result[1]}


@router.get("/risk-analysis")
async def route_risk_analysis(
    request: Request,
    bbox: str = Query(..., description="south,west,north,east"),
    user: dict = Depends(get_current_user),
):
    """Compute overall route risk for all road segments inside a bounding box."""
    db = get_db()
    parts = [float(x) for x in bbox.split(",")]
    if len(parts) != 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="bbox must have 4 values")
    sw, ne = (parts[1], parts[0]), (parts[3], parts[2])
    query = {
        "geometry": {
            "$geoIntersects": {
                "$geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [sw[0], sw[1]],
                        [ne[0], sw[1]],
                        [ne[0], ne[1]],
                        [sw[0], ne[1]],
                        [sw[0], sw[1]],
                    ]],
                },
            }
        }
    }
    segments = await db.road_segments.find(query).to_list(length=500)
    return risk_engine.score_route([{"features": seg.get("risk_factors", {})} for seg in segments])
