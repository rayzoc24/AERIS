"""Signal preemption models."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

SIGNAL_STATES = {"green", "red", "flash", "reverted"}


class SignalPreemptionCreate(BaseModel):
    trip_id: str
    signal_id: str = Field(min_length=1, max_length=64)
    target_state: str = "green"

    @field_validator("target_state")
    @classmethod
    def _validate_state(cls, v: str) -> str:
        if v not in SIGNAL_STATES:
            raise ValueError(f"Invalid signal state. Allowed: {sorted(SIGNAL_STATES)}")
        return v


class SignalWatchdogUpdate(BaseModel):
    """Manual override / watchdog trigger."""
    signal_id: str
    reason: str = Field(min_length=1, max_length=200)
    force_revert: bool = False


class SignalPreemptionOut(BaseModel):
    id: str
    trip_id: str
    signal_id: str
    state: str
    triggered_at: datetime
    reverted_at: Optional[datetime]
    watchdog_active: bool
