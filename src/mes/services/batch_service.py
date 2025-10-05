"""Business logic for managing batch execution records."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import JSON, Column, DateTime, Enum, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..config import MESSettings
from ..models import BatchRecord, BatchStatus

LOGGER = logging.getLogger(__name__)
Base = declarative_base()


class BatchRecordORM(Base):
    """SQLAlchemy ORM mapping for batch records."""

    __tablename__ = "batch_records"

    batch_id = Column(String, primary_key=True)
    recipe_id = Column(String, nullable=False)
    status = Column(Enum(BatchStatus), nullable=False, default=BatchStatus.PLANNED)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    data = Column(JSON, nullable=False, default=dict)
    equipment = Column(JSON, nullable=False, default=list)


class BatchService:
    """Persist and retrieve MES batch records."""

    def __init__(self, settings: MESSettings) -> None:
        self._engine = create_engine(settings.database.url, future=True)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    def upsert_record(self, record: BatchRecord) -> BatchRecord:
        """Insert or update a batch record."""

        with self._session_factory() as session:
            LOGGER.debug("Upserting batch record %s", record.batch_id)
            orm = session.get(BatchRecordORM, record.batch_id)
            if orm is None:
                orm = BatchRecordORM(batch_id=record.batch_id)
            orm.recipe_id = record.recipe_id
            orm.status = record.status
            orm.started_at = record.started_at
            orm.completed_at = record.completed_at
            orm.data = record.data
            orm.equipment = record.equipment
            session.merge(orm)
            session.commit()
        return record

    def list_records(self) -> List[BatchRecord]:
        """Return all batch records."""

        with self._session_factory() as session:
            return [self._to_model(row) for row in session.query(BatchRecordORM).all()]

    def update_status(self, batch_id: str, status: BatchStatus, *, timestamp: datetime | None = None) -> BatchRecord:
        """Update the status of a batch record and optionally timestamps."""

        with self._session_factory() as session:
            orm = session.get(BatchRecordORM, batch_id)
            if orm is None:
                raise KeyError(f"Batch record {batch_id} not found")
            orm.status = status
            if status == BatchStatus.IN_PROGRESS and timestamp:
                orm.started_at = timestamp
            if status in {BatchStatus.COMPLETED, BatchStatus.ABORTED, BatchStatus.HALTED} and timestamp:
                orm.completed_at = timestamp
            session.commit()
            session.refresh(orm)
            return self._to_model(orm)

    def get(self, batch_id: str) -> BatchRecord:
        """Fetch a single batch record."""

        with self._session_factory() as session:
            orm = session.get(BatchRecordORM, batch_id)
            if orm is None:
                raise KeyError(f"Batch record {batch_id} not found")
            return self._to_model(orm)

    @staticmethod
    def _to_model(orm: BatchRecordORM) -> BatchRecord:
        return BatchRecord(
            batch_id=orm.batch_id,
            recipe_id=orm.recipe_id,
            status=orm.status,
            started_at=orm.started_at,
            completed_at=orm.completed_at,
            data=orm.data or {},
            equipment=list(orm.equipment or []),
        )


def record_from_template(template: Dict[str, Any], batch_id: str) -> BatchRecord:
    """Create a batch record instance from a QMIB template payload."""

    recipe_id = template.get("id", "unknown-recipe")
    default_data = template.get("defaultData", {})
    equipment = template.get("equipment", [])
    return BatchRecord(batch_id=batch_id, recipe_id=recipe_id, data=default_data, equipment=equipment)


__all__ = ["BatchService", "BatchRecordORM", "record_from_template"]
