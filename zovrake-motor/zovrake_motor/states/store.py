"""Almacenamiento in-memory de estados por solicitud."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.states.exceptions import ProcessNotFoundError
from zovrake_motor.states.models import ProcessStateRecord


class StateStore:
    """
    Almacén central de estados — cada solicitud mantiene su registro independiente.

    Preparado para miles de procesos simultáneos sin estado global compartido.
    """

    def __init__(self) -> None:
        self._records: dict[UUID, ProcessStateRecord] = {}

    def save(self, record: ProcessStateRecord) -> None:
        self._records[record.process_id] = record

    def get(self, process_id: UUID) -> ProcessStateRecord | None:
        return self._records.get(process_id)

    def require(self, process_id: UUID) -> ProcessStateRecord:
        record = self.get(process_id)
        if record is None:
            raise ProcessNotFoundError(f"Proceso no encontrado: {process_id}")
        return record

    def exists(self, process_id: UUID) -> bool:
        return process_id in self._records

    def list_process_ids(self) -> list[UUID]:
        return list(self._records.keys())

    def count(self) -> int:
        return len(self._records)
