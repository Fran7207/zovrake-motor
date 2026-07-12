"""Almacén de auditoría en memoria — sin persistencia."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.svaf.models import AuditRecord


class AuditStore:
    """Registro centralizado de auditoría — aislado por proceso."""

    def __init__(self) -> None:
        self._records: dict[str, AuditRecord] = {}
        self._by_process: dict[UUID, list[str]] = {}

    def save(self, record: AuditRecord) -> None:
        self._records[record.audit_id] = record
        self._by_process.setdefault(record.process_id, [])
        if record.audit_id not in self._by_process[record.process_id]:
            self._by_process[record.process_id].append(record.audit_id)

    def get(self, audit_id: str) -> AuditRecord | None:
        return self._records.get(audit_id)

    def by_process(self, process_id: UUID) -> tuple[AuditRecord, ...]:
        ids = self._by_process.get(process_id, [])
        return tuple(self._records[audit_id] for audit_id in ids)

    def count(self) -> int:
        return len(self._records)

    def snapshot(self) -> list[dict]:
        return [record.to_dict() for record in self._records.values()]
