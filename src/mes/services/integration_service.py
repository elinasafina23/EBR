"""Service orchestrating communication between MES components and QMIB."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict

from ..config import MESSettings
from ..connectors.qmib_client import QMIBClient
from ..models import BatchRecord, BatchStatus, EventAcknowledgement
from .batch_service import BatchService, record_from_template

LOGGER = logging.getLogger(__name__)


class IntegrationService:
    """High-level orchestration service for MES-QMIB interactions."""

    def __init__(self, settings: MESSettings, batch_service: BatchService | None = None) -> None:
        self._settings = settings
        self._batch_service = batch_service or BatchService(settings)

    async def synchronize_batch_from_template(self, template_id: str, batch_id: str) -> BatchRecord:
        """Fetch template from QMIB and create local batch record."""

        async with QMIBClient(self._settings) as client:
            template_payload = await client.fetch_batch_template(template_id)
        record = record_from_template(template_payload, batch_id)
        return self._batch_service.upsert_record(record)

    async def publish_batch_completion(self, batch_id: str) -> Dict[str, str]:
        """Send completed batch payload to QMIB."""

        record = self._batch_service.get(batch_id)
        if record.status != BatchStatus.COMPLETED:
            raise ValueError("Only completed batch records can be published to QMIB")
        payload = record.model_dump()
        async with QMIBClient(self._settings) as client:
            response = await client.publish_batch_record(payload)
        return response

    async def update_batch_status(self, batch_id: str, status: BatchStatus) -> BatchRecord:
        """Update local record and synchronize metadata."""

        timestamp = datetime.utcnow()
        record = self._batch_service.update_status(batch_id, status, timestamp=timestamp)
        if status == BatchStatus.COMPLETED:
            await self.publish_batch_completion(batch_id)
        return record

    async def acknowledge_event(self, acknowledgement: EventAcknowledgement) -> Dict[str, str]:
        """Acknowledge QMIB event/alarm."""

        async with QMIBClient(self._settings) as client:
            response = await client.acknowledge_event(
                acknowledgement.event_id,
                acknowledgement.model_dump(),
            )
        return response


__all__ = ["IntegrationService"]
