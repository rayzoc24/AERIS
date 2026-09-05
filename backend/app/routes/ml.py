"""ML risk engine routes (feature #5)."""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.security.rbac import get_current_user, require_roles, Role
from app.services.ml_engine import risk_engine

logger = logging.getLogger("aeris.ml")
router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/score-segment")
async def score_segment(
    request: Request,
    features: Dict,
    user: dict = Depends(get_current_user),
):
    return {
        "risk_score": risk_engine.score_segment(features),
        "version": risk_engine.version,
        "features_received": list(features.keys()),
    }


@router.post("/score-route")
async def score_route(
    request: Request,
    segments: List[Dict],
    user: dict = Depends(get_current_user),
):
    return risk_engine.score_route(segments)


@router.get("/version")
async def model_version(request: Request, user: dict = Depends(get_current_user)):
    return {"version": risk_engine.version}


@router.post("/reload")
async def reload_model(
    request: Request,
    user: dict = Depends(require_roles(Role.ADMIN)),
):
    """Admin endpoint to reload the trained model file."""
    from pathlib import Path
    body = await request.json()
    path_str = body.get("model_path")
    if not path_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="model_path required")
    path = Path(path_str)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model file not found")
    risk_engine.load_model(path)
    return {"version": risk_engine.version, "path": str(path)}
