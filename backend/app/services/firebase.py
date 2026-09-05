"""Firebase Cloud Messaging client for 500m heading-filtered alerts.

Heading filtering ensures that only vehicles ahead of the ambulance in
the ambulance's lane receive the alert. We compute the heading between
the ambulance and each candidate vehicle and skip those behind.

Google shut down the legacy `fcm.googleapis.com/fcm/send` + server-key
endpoint in June 2024. This client uses the current FCM HTTP v1 API via
the `firebase-admin` SDK (already in requirements.txt), authenticated
with a service account JSON file pointed to by FIREBASE_CREDENTIALS_PATH.
Until that env var is set, sends are skipped (logged, not raised) so the
rest of the system keeps working without push notifications configured.
"""
from __future__ import annotations

import asyncio
import logging
import math
from typing import List, Optional

from app.config import get_settings

logger = logging.getLogger("aeris.firebase")


def _haversine_m(p1, p2) -> float:
    lon1, lat1 = p1
    lon2, lat2 = p2
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _heading_deg(p1, p2) -> float:
    lon1, lat1 = p1
    lon2, lat2 = p2
    x = math.cos(math.radians(lat2)) * math.sin(math.radians(lon2 - lon1))
    y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1))
    return (math.degrees(math.atan2(x, y)) + 360) % 360


class FirebaseClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._credentials_path = settings.FIREBASE_CREDENTIALS_PATH
        self._app = None
        if self._credentials_path:
            self._init_app()
        else:
            logger.warning(
                "FIREBASE_CREDENTIALS_PATH not set - heading-filtered push "
                "alerts are disabled until a service account JSON is added."
            )

    def _init_app(self) -> None:
        try:
            import firebase_admin
            from firebase_admin import credentials

            cred = credentials.Certificate(self._credentials_path)
            self._app = firebase_admin.initialize_app(cred)
        except Exception as exc:  # noqa: BLE001 - never let push setup crash boot
            logger.error("Failed to initialise Firebase Admin SDK: %s", type(exc).__name__)
            self._app = None

    async def close(self) -> None:
        if self._app is not None:
            import firebase_admin

            firebase_admin.delete_app(self._app)
            self._app = None

    async def send_heading_filtered_alert(
        self,
        ambulance_position,
        ambulance_heading_deg: float,
        candidate_vehicles: List[dict],
        radius_m: float = 500.0,
        heading_tolerance_deg: float = 35.0,
    ) -> int:
        """Return number of vehicles that received the alert."""
        if self._app is None:
            logger.warning("Firebase not configured, skipping push alerts")
            return 0

        sent = 0
        for vehicle in candidate_vehicles:
            pos = vehicle.get("position")
            if not pos or len(pos) != 2:
                continue
            dist = _haversine_m(ambulance_position, pos)
            if dist > radius_m:
                continue
            heading = _heading_deg(ambulance_position, pos)
            diff = abs((heading - ambulance_heading_deg + 540) % 360 - 180)
            if diff > heading_tolerance_deg:
                continue
            if await self._send_to_token(vehicle["fcm_token"], vehicle.get("payload", {})):
                sent += 1
        return sent

    async def _send_to_token(self, token: str, payload: dict) -> bool:
        try:
            from firebase_admin import messaging

            message = messaging.Message(
                token=token,
                notification=messaging.Notification(
                    title="Emergency vehicle approaching",
                    body="Please clear the lane for an ambulance.",
                ),
                data={str(k): str(v) for k, v in payload.items()},
                android=messaging.AndroidConfig(priority="high"),
            )
            # firebase-admin's messaging.send() is a blocking network call;
            # run it off the event loop so one push doesn't stall requests.
            await asyncio.to_thread(messaging.send, message, app=self._app)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("FCM send failed: %s", type(exc).__name__)
            return False


firebase_client = FirebaseClient()
