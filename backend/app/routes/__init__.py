"""AERIS API route modules."""
from app.routes import (
    auth,
    health,
    dispatch,
    routes_api,
    signals,
    hazards,
    citizens,
    ml,
    security,
    websocket,
)

ROUTERS = [
    ("health", health.router),
    ("security", security.router),
    ("auth", auth.router),
    ("dispatch", dispatch.router),
    ("routes", routes_api.router),
    ("signals", signals.router),
    ("hazards", hazards.router),
    ("citizens", citizens.router),
    ("ml", ml.router),
    ("ws", websocket.router),
]
