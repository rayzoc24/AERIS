"""MongoDB async connection layer.

Uses Motor (async PyMongo driver) to prevent NoSQL injection through
parameterised queries and explicit schema validation.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger("aeris.database")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


# MongoDB JSON schema validators (security check #10 - DB rules).
# These run at the database layer so malicious writes through any client
# (compass, shell, other services) are still rejected.
COLLECTION_VALIDATORS: Dict[str, Dict[str, Any]] = {
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["email", "password_hash", "role", "created_at"],
            "properties": {
                "email": {"bsonType": "string", "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"},
                "password_hash": {"bsonType": "string", "minLength": 32},
                "role": {"enum": ["admin", "driver", "citizen"]},
                "name": {"bsonType": "string", "maxLength": 120},
                "is_active": {"bsonType": "bool"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "vehicles": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["registration_number", "type", "status"],
            "properties": {
                "registration_number": {"bsonType": "string", "maxLength": 20},
                "type": {"enum": ["ambulance", "fire", "police", "rescue"]},
                "status": {"enum": ["available", "dispatched", "en_route", "on_scene", "offline"]},
                "driver_id": {"bsonType": ["objectId", "null"]},
                "current_trip_id": {"bsonType": ["objectId", "null"]},
                "last_known_location": {
                    "bsonType": ["object", "null"],
                    "properties": {
                        "type": {"enum": ["Point"]},
                        "coordinates": {
                            "bsonType": "array",
                            "items": {"bsonType": "double"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },
            },
        }
    },
    "road_segments": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["segment_id", "geometry", "risk_score"],
            "properties": {
                "segment_id": {"bsonType": "string"},
                "geometry": {"bsonType": "object"},
                "risk_score": {"bsonType": "double", "minimum": 0, "maximum": 1},
                "risk_factors": {"bsonType": "object"},
                "blackspot": {"bsonType": "bool"},
                "last_updated": {"bsonType": "date"},
            },
        }
    },
    "hazards": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["type", "location", "reported_by", "created_at"],
            "properties": {
                "type": {"enum": ["accident", "pothole", "flooding", "obstruction", "road_work", "vehicle_breakdown"]},
                "location": {
                    "bsonType": "object",
                    "required": ["type", "coordinates"],
                    "properties": {
                        "type": {"enum": ["Point"]},
                        "coordinates": {"bsonType": "array", "minItems": 2, "maxItems": 2},
                    },
                },
                "severity": {"enum": ["low", "medium", "high", "critical"]},
                "status": {"enum": ["active", "verified", "resolved", "dismissed"]},
                "corroboration_score": {"bsonType": "double", "minimum": 0, "maximum": 1},
                "reported_by": {"bsonType": "objectId"},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "trips": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["vehicle_id", "status", "started_at"],
            "properties": {
                "vehicle_id": {"bsonType": "objectId"},
                "driver_id": {"bsonType": ["objectId", "null"]},
                "status": {"enum": ["pending", "active", "completed", "cancelled"]},
                "origin": {"bsonType": "object"},
                "destination": {"bsonType": "object"},
                "route_polyline": {"bsonType": ["string", "null"]},
                "green_corridor": {"bsonType": ["array", "null"]},
                "started_at": {"bsonType": "date"},
                "ended_at": {"bsonType": ["date", "null"]},
            },
        }
    },
    "signal_preemptions": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["trip_id", "signal_id", "state", "triggered_at"],
            "properties": {
                "trip_id": {"bsonType": "objectId"},
                "signal_id": {"bsonType": "string"},
                "state": {"enum": ["green", "red", "flash", "reverted"]},
                "triggered_at": {"bsonType": "date"},
                "reverted_at": {"bsonType": ["date", "null"]},
                "watchdog_active": {"bsonType": "bool"},
            },
        }
    },
}


async def init_db() -> AsyncIOMotorDatabase:
    """Initialise the MongoDB client and ensure schema validators exist."""
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    _db = _client[settings.MONGO_DB_NAME]

    await _client.admin.command("ping")

    for collection_name, validator in COLLECTION_VALIDATORS.items():
        existing = await _db.list_collections(filter={"name": collection_name})
        if await existing.to_list(length=1):
            await _db.command(
                "collMod",
                collection_name,
                validator=validator,
                validationLevel="strict",
            )
        else:
            await _db.create_collection(collection_name, validator=validator, validationLevel="strict")

    await _ensure_indexes(_db)
    logger.info("MongoDB initialised: %s", settings.MONGO_DB_NAME)
    return _db


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("email", unique=True)
    await db.vehicles.create_index("registration_number", unique=True)
    await db.road_segments.create_index("segment_id", unique=True)
    await db.road_segments.create_index([("geometry", "2dsphere")])
    await db.hazards.create_index([("location", "2dsphere")])
    await db.hazards.create_index("status")
    await db.hazards.create_index("created_at")
    await db.trips.create_index("vehicle_id")
    await db.trips.create_index("status")
    await db.signal_preemptions.create_index([("trip_id", 1), ("signal_id", 1)])


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised. Call init_db() at startup.")
    return _db


async def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
