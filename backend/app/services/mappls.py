"""Mappls API client (routing, traffic, ETA, geocoding).

Mappls moved to a simpler authentication model in August 2025: a static
REST API key is sent as an `access_token` query parameter on every
request, replacing the old OAuth2 client_credentials token exchange for
most REST endpoints. See:
  https://github.com/mappls-api/mappls-rest-apis (main branch = new auth)

We use that static-key model whenever MAPPLS_API_KEY is configured -
this is what the Mappls dashboard issues by default today. If only
MAPPLS_CLIENT_ID / MAPPLS_CLIENT_SECRET are set (older Mappls accounts
provisioned before the migration), we fall back to the legacy OAuth2
client_credentials flow. Either way the key/secret is never logged or
echoed back in error responses.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import get_settings

logger = logging.getLogger("aeris.mappls")

# Current (Aug 2025+) endpoints - static access_token query param.
_ROUTE_BASE_URL = "https://route.mappls.com/route/direction"
_GEOCODE_URL = "https://apis.mappls.com/advancedmaps/v1/{key}/geo_code"

# Legacy OAuth2 endpoints - kept for accounts still on the old flow.
_LEGACY_TOKEN_URL = "https://outpost.mappls.com/api/security/oauth/token"
_LEGACY_BASE_URL = "https://apis.mappls.com/advancedmaps/v1"


class MapplsAuthError(RuntimeError):
    """Raised when Mappls credentials are missing or rejected."""


class MapplsClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.MAPPLS_API_KEY
        self._client_id = settings.MAPPLS_CLIENT_ID
        self._client_secret = settings.MAPPLS_CLIENT_SECRET
        self._use_static_key = bool(self._api_key)
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._http = httpx.AsyncClient(timeout=10.0)

        if not self._use_static_key and not (self._client_id and self._client_secret):
            logger.warning(
                "Mappls is not configured (no MAPPLS_API_KEY and no "
                "MAPPLS_CLIENT_ID/MAPPLS_CLIENT_SECRET). Routing, traffic "
                "and geocoding calls will fail until .env is filled in."
            )

    async def close(self) -> None:
        await self._http.aclose()

    # -- Authentication ---------------------------------------------------------

    async def _auth_params(self) -> Dict[str, str]:
        """Return the query params needed to authenticate a request."""
        if self._use_static_key:
            return {"access_token": self._api_key}
        token = await self._legacy_token()
        return {"access_token": token}

    async def _legacy_token(self) -> str:
        """OAuth2 client_credentials flow for accounts without a static key."""
        if not (self._client_id and self._client_secret):
            raise MapplsAuthError(
                "Mappls is not configured. Set MAPPLS_API_KEY (preferred) or "
                "MAPPLS_CLIENT_ID/MAPPLS_CLIENT_SECRET in backend/.env."
            )
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token
        resp = await self._http.post(
            _LEGACY_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        resp.raise_for_status()
        body = resp.json()
        token = body.get("access_token")
        if not token:
            raise MapplsAuthError("Mappls OAuth token response did not include access_token")
        self._token = token
        # Refresh a little early; default to 23h if Mappls omits expires_in.
        expires_in = int(body.get("expires_in", 82800))
        self._token_expires_at = time.monotonic() + max(expires_in - 60, 60)
        return token

    async def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        auth_params = await self._auth_params()
        resp = await self._http.get(url, params={**params, **auth_params})
        if resp.status_code == 401 and not self._use_static_key:
            # Legacy token may have been revoked server-side; refresh once.
            self._token = None
            auth_params = await self._auth_params()
            resp = await self._http.get(url, params={**params, **auth_params})
        resp.raise_for_status()
        return resp.json()

    # -- Public API ---------------------------------------------------------------

    async def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        avoid: Optional[List[str]] = None,
        via: Optional[List[Tuple[float, float]]] = None,
    ) -> Dict[str, Any]:
        """Return route geometry, distance, and ETA with live traffic.

        Coordinates are (longitude, latitude) tuples, matching the rest of
        this codebase's GeoJSON convention.
        """
        waypoints = [origin, *(via or []), destination]
        coord_path = ";".join(f"{lon},{lat}" for lon, lat in waypoints)
        params: Dict[str, Any] = {
            "geometries": "polyline",
            "steps": "true",
            "overview": "full",
            "rtype": 1,  # 0 = shortest, 1 = fastest / traffic-aware
        }
        if avoid:
            params["avoid_all"] = ",".join(avoid)
        url = f"{_ROUTE_BASE_URL}/route_adv/driving/{coord_path}"
        return await self._get(url, params)

    async def get_traffic(self, bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
        """Fetch live traffic conditions for the bounding box.

        Mappls does not expose a standalone "traffic incidents in a box"
        REST endpoint on the standard plan; traffic-aware ETA data comes
        back as part of route_adv above. This helper degrades gracefully
        (empty incident list) instead of raising, so a dashboard tile
        never crashes the page if the account's plan doesn't include this
        add-on - contact Mappls support to enable the Traffic API if
        incident-level data is required for the hackathon demo.
        """
        south, west, north, east = bbox
        try:
            data = await self._get(
                f"{_ROUTE_BASE_URL}/route_eta/driving/{west},{south};{east},{north}",
                {"region": "IND"},
            )
            return {"incidents": data.get("incidents", []), "raw": data}
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Mappls traffic endpoint returned %s - check that Traffic "
                "API access is enabled for this key.",
                exc.response.status_code,
            )
            return {"incidents": [], "raw": None}

    async def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        url = _GEOCODE_URL.format(key=self._api_key) if self._use_static_key else f"{_LEGACY_BASE_URL}/geo_code"
        data = await self._get(url, {"addr": address})
        results = data.get("copResults") or data.get("results") or []
        if not results:
            return None
        first = results[0]
        lon = first.get("longitude", first.get("lng"))
        lat = first.get("latitude", first.get("lat"))
        if lon is None or lat is None:
            return None
        return float(lon), float(lat)


mappls_client = MapplsClient()
