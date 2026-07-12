"""Almacén de cola lógica en memoria — sin infraestructura externa."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.apqm.enums import ApqmProcessingStage
from zovrake_motor.enterprise_integration.apqm.models import QueueItemRecord


class ApqmQueueStore:
    """Cola lógica FIFO con índice por proceso — aislamiento total entre procesos."""

    def __init__(self) -> None:
        self._items: dict[str, QueueItemRecord] = {}
        self._fifo: list[str] = []
        self._by_process: dict[UUID, str] = {}

    def save(self, record: QueueItemRecord) -> None:
        self._items[record.item_id] = record
        if record.item_id not in self._fifo:
            self._fifo.append(record.item_id)
        self._by_process[record.context.process_id] = record.item_id

    def get(self, item_id: str) -> QueueItemRecord | None:
        return self._items.get(item_id)

    def get_by_process(self, process_id: UUID) -> QueueItemRecord | None:
        item_id = self._by_process.get(process_id)
        if item_id is None:
            return None
        return self._items.get(item_id)

    def pending_items(self) -> tuple[QueueItemRecord, ...]:
        pending_stages = {
            ApqmProcessingStage.REQUEST_RECEIVED,
            ApqmProcessingStage.QUEUED,
        }
        return tuple(
            self._items[item_id]
            for item_id in self._fifo
            if self._items[item_id].stage in pending_stages
        )

    def active_items(self) -> tuple[QueueItemRecord, ...]:
        active_stages = {
            ApqmProcessingStage.ASSIGNED,
            ApqmProcessingStage.PROCESSING_STARTED,
            ApqmProcessingStage.PROCESSING_IN_EXECUTION,
        }
        return tuple(
            record for record in self._items.values() if record.stage in active_stages
        )

    def all_items(self) -> tuple[QueueItemRecord, ...]:
        return tuple(self._items[item_id] for item_id in self._fifo)

    def count(self) -> int:
        return len(self._items)

    def pending_count(self) -> int:
        return len(self.pending_items())

    def active_count(self) -> int:
        return len(self.active_items())

    def queue_position(self, item_id: str) -> int:
        pending = self.pending_items()
        for index, record in enumerate(pending, start=1):
            if record.item_id == item_id:
                return index
        return 0

    def snapshot(self) -> list[dict]:
        return [record.to_dict() for record in self.all_items()]
