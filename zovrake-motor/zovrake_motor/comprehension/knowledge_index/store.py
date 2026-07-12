"""Almacén en memoria del índice documental."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.knowledge_index.exceptions import DuplicateIndexEntryError
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexEntry


class KnowledgeIndexStore:
    """
    Almacén interno del índice documental — sin persistencia.

    Preparado para escalabilidad y crecimiento del Motor Inteligente.
    """

    def __init__(self) -> None:
        self._entries_by_index_id: dict[str, DocumentIndexEntry] = {}
        self._entries_by_model_id: dict[str, str] = {}

    def register(self, entry: DocumentIndexEntry) -> None:
        if entry.traceability.model_id in self._entries_by_model_id:
            raise DuplicateIndexEntryError(
                f"Modelo ya indexado: {entry.traceability.model_id}",
            )
        self._entries_by_index_id[entry.index_id] = entry
        self._entries_by_model_id[entry.traceability.model_id] = entry.index_id

    def get_by_index_id(self, index_id: str) -> DocumentIndexEntry | None:
        return self._entries_by_index_id.get(index_id)

    def get_by_model_id(self, model_id: str) -> DocumentIndexEntry | None:
        index_id = self._entries_by_model_id.get(model_id)
        if index_id is None:
            return None
        return self._entries_by_index_id.get(index_id)

    def count(self) -> int:
        return len(self._entries_by_index_id)

    def all_entries(self) -> tuple[DocumentIndexEntry, ...]:
        return tuple(self._entries_by_index_id.values())

    def snapshot(self) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in self._entries_by_index_id.values()]
