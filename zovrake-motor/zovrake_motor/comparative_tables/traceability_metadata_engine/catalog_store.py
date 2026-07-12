"""Almacén en memoria de catálogos enriquecidos del TME."""

from __future__ import annotations

from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    EnrichedComparativeTableCatalog,
)


class EnrichedComparativeTableCatalogStore:
    """Persistencia en memoria de catálogos enriquecidos — sin almacenamiento persistente."""

    def __init__(self) -> None:
        self._catalogs: list[EnrichedComparativeTableCatalog] = []

    def save(self, catalog: EnrichedComparativeTableCatalog) -> None:
        self._catalogs.append(catalog)

    def all_catalogs(self) -> tuple[EnrichedComparativeTableCatalog, ...]:
        return tuple(self._catalogs)

    def count(self) -> int:
        return len(self._catalogs)

    def snapshot(self) -> dict[str, int]:
        return {"catalog_entries_count": self.count()}
