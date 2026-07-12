"""Almacén en memoria de asociaciones de contexto."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.context_integration.exceptions import DuplicateContextAssociationError
from zovrake_motor.comprehension.context_integration.models import ContextAssociation


class ContextIntegrationStore:
    """
    Almacén interno de asociaciones de contexto — sin persistencia.

    Preparado para escalabilidad y crecimiento del Motor Inteligente.
    """

    def __init__(self) -> None:
        self._associations_by_id: dict[str, ContextAssociation] = {}
        self._associations_by_process_document: dict[str, str] = {}
        self._index_context_map: dict[str, str] = {}

    def _process_document_key(self, process_id: UUID, document_id: str) -> str:
        return f"{process_id}:{document_id}"

    def register(self, association: ContextAssociation) -> None:
        key = self._process_document_key(
            association.traceability.process_id,
            association.traceability.document_id,
        )
        if key in self._associations_by_process_document:
            raise DuplicateContextAssociationError(
                f"Contexto ya asociado: {association.traceability.document_id}",
            )
        self._associations_by_id[association.association_id] = association
        self._associations_by_process_document[key] = association.association_id
        self._index_context_map[association.traceability.index_id] = association.traceability.context_id

    def get_by_association_id(self, association_id: str) -> ContextAssociation | None:
        return self._associations_by_id.get(association_id)

    def get_by_process_document(self, process_id: UUID, document_id: str) -> ContextAssociation | None:
        association_id = self._associations_by_process_document.get(
            self._process_document_key(process_id, document_id),
        )
        if association_id is None:
            return None
        return self._associations_by_id.get(association_id)

    def get_context_id_by_index(self, index_id: str) -> str | None:
        return self._index_context_map.get(index_id)

    def count(self) -> int:
        return len(self._associations_by_id)

    def all_associations(self) -> tuple[ContextAssociation, ...]:
        return tuple(self._associations_by_id.values())

    def snapshot(self) -> list[dict[str, Any]]:
        return [association.to_dict() for association in self._associations_by_id.values()]

    def index_associations_snapshot(self) -> dict[str, str]:
        return dict(self._index_context_map)
