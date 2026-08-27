"""Almacén en memoria del índice documental."""

from __future__ import annotations

from threading import Lock
from typing import Any

from zovrake_motor.comprehension.knowledge_index.exceptions import (
    DuplicateIndexEntryError,
)
from zovrake_motor.comprehension.knowledge_index.models import (
    DocumentIndexEntry,
)


class KnowledgeIndexStore:
    """
    Almacén interno del índice documental — sin persistencia.

    Preparado para escalabilidad y crecimiento del Motor Inteligente.

    El índice distingue entre:

    - una duplicación real del mismo modelo dentro del mismo proceso;
    - la reutilización legítima de un modelo ya indexado desde otro proceso.

    El registro se protege mediante un lock para que la decisión de
    registrar o reutilizar sea atómica frente a análisis concurrentes.
    """

    def __init__(self) -> None:
        self._entries_by_index_id: dict[str, DocumentIndexEntry] = {}
        self._entries_by_model_id: dict[str, str] = {}
        self._lock = Lock()

    def register(
        self,
        entry: DocumentIndexEntry,
    ) -> DocumentIndexEntry:
        """
        Registra una entrada o reutiliza una entrada existente.

        La misma entrada documental dentro del mismo proceso se considera
        un duplicado real y conserva el comportamiento de protección
        mediante DuplicateIndexEntryError.

        Si el mismo modelo ya fue indexado por otro proceso, se reutiliza
        la entrada existente en lugar de volver a registrarla.
        """
        with self._lock:
            existing_index_id = self._entries_by_model_id.get(
                entry.traceability.model_id,
            )

            if existing_index_id is not None:
                existing_entry = self._entries_by_index_id[
                    existing_index_id
                ]

                if (
                    existing_entry.traceability.process_id
                    == entry.traceability.process_id
                ):
                    raise DuplicateIndexEntryError(
                        f"Modelo ya indexado: "
                        f"{entry.traceability.model_id}",
                    )

                return existing_entry

            self._entries_by_index_id[
                entry.index_id
            ] = entry

            self._entries_by_model_id[
                entry.traceability.model_id
            ] = entry.index_id

            return entry

    def get_by_index_id(
        self,
        index_id: str,
    ) -> DocumentIndexEntry | None:
        with self._lock:
            return self._entries_by_index_id.get(
                index_id,
            )

    def get_by_model_id(
        self,
        model_id: str,
    ) -> DocumentIndexEntry | None:
        with self._lock:
            index_id = self._entries_by_model_id.get(
                model_id,
            )

            if index_id is None:
                return None

            return self._entries_by_index_id.get(
                index_id,
            )

    def count(self) -> int:
        with self._lock:
            return len(
                self._entries_by_index_id,
            )

    def all_entries(
        self,
    ) -> tuple[DocumentIndexEntry, ...]:
        with self._lock:
            return tuple(
                self._entries_by_index_id.values(),
            )

    def snapshot(
        self,
    ) -> list[dict[str, Any]]:
        with self._lock:
            return [
                entry.to_dict()
                for entry in self._entries_by_index_id.values()
            ]
