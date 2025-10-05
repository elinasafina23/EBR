"""Domain models shared across the MES service."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BatchStatus(str, Enum):
    """Lifecycle states for a batch execution."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    HALTED = "halted"
    ABORTED = "aborted"


class BatchRecord(BaseModel):
    """Representation of a batch record tracked by the MES."""

    batch_id: str = Field(..., description="Unique identifier for the batch instance.")
    recipe_id: str = Field(..., description="Identifier of the recipe or template executed.")
    status: BatchStatus = Field(BatchStatus.PLANNED, description="Current execution status.")
    started_at: Optional[datetime] = Field(None, description="Timestamp when execution started.")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when execution completed.")
    data: Dict[str, str | float | int | bool | None] = Field(
        default_factory=dict,
        description="Additional contextual data captured during the batch.",
    )
    equipment: List[str] = Field(default_factory=list, description="Equipment identifiers involved in the batch.")


class EquipmentState(BaseModel):
    """Represents the current state of a single equipment item."""

    equipment_id: str
    status: str
    measured_at: datetime
    attributes: Dict[str, str | float | int | bool | None] = Field(default_factory=dict)


class EventAcknowledgement(BaseModel):
    """Payload for acknowledging an event in QMIB."""

    event_id: str
    acknowledged_by: str
    comment: Optional[str] = None
    acknowledged_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    "BatchRecord",
    "BatchStatus",
    "EquipmentState",
    "EventAcknowledgement",
]
