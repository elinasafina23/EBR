"""Client wrapper for AspenTech system:inmation QMIB interactions."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import MESSettings

LOGGER = logging.getLogger(__name__)


class QMIBAuthenticationError(RuntimeError):
    """Raised when QMIB returns an authentication failure."""


class QMIBClient:
    """Abstraction over QMIB REST/HTTP endpoints."""

    def __init__(self, settings: MESSettings, client: Optional[httpx.AsyncClient] = None) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(
            base_url=str(settings.qmib.base_url),
            verify=settings.qmib.verify_ssl,
            timeout=settings.qmib.timeout_seconds,
        )

    async def __aenter__(self) -> "QMIBClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()

    async def close(self) -> None:
        """Close underlying HTTP client."""

        await self._client.aclose()

    async def _request(self, method: str, endpoint: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a REST call against QMIB with retry semantics."""

        headers = {"Content-Type": "application/json"}
        auth = (self._settings.qmib.username, self._settings.qmib.password)

        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=1, min=1, max=8),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,
        ):
            with attempt:
                LOGGER.debug("QMIB %s %s payload=%s", method, endpoint, json)
                response = await self._client.request(method, endpoint, json=json, headers=headers, auth=auth)

        if response.status_code == httpx.codes.UNAUTHORIZED:
            raise QMIBAuthenticationError("Authentication to QMIB failed. Check credentials.")

        response.raise_for_status()
        if response.content:
            return response.json()
        return None

    async def fetch_equipment_state(self, equipment_id: str) -> Dict[str, Any]:
        """Retrieve live state for a specific equipment from QMIB."""

        return await self._request("GET", f"/equipment/{equipment_id}")

    async def publish_batch_record(self, batch_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a batch execution record to QMIB for archival."""

        return await self._request("POST", "/batches", json=batch_payload)

    async def fetch_batch_template(self, template_id: str) -> Dict[str, Any]:
        """Request a batch template definition from QMIB."""

        return await self._request("GET", f"/templates/{template_id}")

    async def acknowledge_event(self, event_id: str, acknowledgement: Dict[str, Any]) -> Dict[str, Any]:
        """Acknowledge an event or alarm in QMIB."""

        return await self._request("POST", f"/events/{event_id}/acknowledge", json=acknowledgement)


__all__ = ["QMIBClient", "QMIBAuthenticationError"]
