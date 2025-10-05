"""FastAPI routes exposing MES functionality."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..config import MESSettings, get_settings
from ..models import BatchRecord, BatchStatus, EventAcknowledgement
from ..services.batch_service import BatchService
from ..services.integration_service import IntegrationService

router = APIRouter(prefix="/api", tags=["mes"])


def get_batch_service(settings: MESSettings = Depends(get_settings)) -> BatchService:
    """Dependency that provides a batch service instance."""

    return BatchService(settings)


def get_integration_service(
    settings: MESSettings = Depends(get_settings),
    batch_service: BatchService = Depends(get_batch_service),
) -> IntegrationService:
    """Dependency that provides integration service."""

    return IntegrationService(settings, batch_service=batch_service)


@router.get("/batches", response_model=list[BatchRecord])
def list_batches(batch_service: BatchService = Depends(get_batch_service)) -> list[BatchRecord]:
    """List all batch records tracked by the MES."""

    return batch_service.list_records()


@router.post("/batches", response_model=BatchRecord)
def create_batch(record: BatchRecord, batch_service: BatchService = Depends(get_batch_service)) -> BatchRecord:
    """Create or replace a batch record."""

    return batch_service.upsert_record(record)


@router.patch("/batches/{batch_id}/status", response_model=BatchRecord)
async def update_status(
    batch_id: str,
    status: BatchStatus,
    integration_service: IntegrationService = Depends(get_integration_service),
) -> BatchRecord:
    """Update the status of a batch record and synchronize with QMIB if necessary."""

    try:
        return await integration_service.update_batch_status(batch_id, status)
    except KeyError as exc:  # pragma: no cover - simple error mapping
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/batches/from-template", response_model=BatchRecord)
async def create_from_template(
    template_id: str,
    batch_id: str,
    integration_service: IntegrationService = Depends(get_integration_service),
) -> BatchRecord:
    """Create a batch record in MES from a QMIB template."""

    return await integration_service.synchronize_batch_from_template(template_id, batch_id)


@router.post("/events/acknowledge")
async def acknowledge_event(
    acknowledgement: EventAcknowledgement,
    integration_service: IntegrationService = Depends(get_integration_service),
) -> dict[str, str]:
    """Acknowledge an event within QMIB."""

    return await integration_service.acknowledge_event(acknowledgement)


__all__ = ["router"]
