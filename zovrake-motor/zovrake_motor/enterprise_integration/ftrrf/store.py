"""Registro de errores en memoria — sin persistencia."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.ftrrf.enums import ErrorCategory, RecoveryStatus
from zovrake_motor.enterprise_integration.ftrrf.models import ErrorRecord


class ErrorRegistryStore:
    """Almacena registros de error aislados por proceso — sin mezclar procesos."""

    def __init__(self) -> None:
        self._records: dict[str, ErrorRecord] = {}
        self._by_process: dict[UUID, list[str]] = {}

    def save(self, record: ErrorRecord) -> None:
        self._records[record.error_id] = record
        self._by_process.setdefault(record.process_id, [])
        if record.error_id not in self._by_process[record.process_id]:
            self._by_process[record.process_id].append(record.error_id)

    def get(self, error_id: str) -> ErrorRecord | None:
        return self._records.get(error_id)

    def by_process(self, process_id: UUID) -> tuple[ErrorRecord, ...]:
        ids = self._by_process.get(process_id, [])
        return tuple(self._records[error_id] for error_id in ids)

    def latest_for_process(self, process_id: UUID) -> ErrorRecord | None:
        records = self.by_process(process_id)
        return records[-1] if records else None

    def count(self) -> int:
        return len(self._records)

    def count_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {category.value: 0 for category in ErrorCategory}
        for record in self._records.values():
            counts[record.category.value] += 1
        return counts

    def count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {status.value: 0 for status in RecoveryStatus}
        for record in self._records.values():
            counts[record.recovery_status.value] += 1
        return counts

    def snapshot(self) -> list[dict]:
        return [record.to_dict() for record in self._records.values()]
