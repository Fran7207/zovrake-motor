"""Almacén en memoria de catálogos de asociación de contexto."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.classification.context_association.models import ContextAssociationCatalog


class ContextAssociationCatalogStore:
    """Almacén temporal de catálogos de asociación — sin persistencia."""

    def __init__(self) -> None:
        self._catalogs_by_id: dict[str, ContextAssociationCatalog] = {}
        self._catalog_ids_by_process: dict[UUID, list[str]] = {}

    def save(self, catalog: ContextAssociationCatalog) -> None:
        self._catalogs_by_id[catalog.catalog_id] = catalog
        process_ids = self._catalog_ids_by_process.setdefault(catalog.process_id, [])
        if catalog.catalog_id not in process_ids:
            process_ids.append(catalog.catalog_id)

    def get(self, catalog_id: str) -> ContextAssociationCatalog | None:
        return self._catalogs_by_id.get(catalog_id)

    def get_by_process(self, process_id: UUID) -> tuple[ContextAssociationCatalog, ...]:
        catalog_ids = self._catalog_ids_by_process.get(process_id, [])
        return tuple(
            catalog
            for catalog_id in catalog_ids
            if (catalog := self._catalogs_by_id.get(catalog_id)) is not None
        )

    def count(self) -> int:
        return len(self._catalogs_by_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "catalog_entries_count": self.count(),
            "processes_with_catalogs": len(self._catalog_ids_by_process),
        }
