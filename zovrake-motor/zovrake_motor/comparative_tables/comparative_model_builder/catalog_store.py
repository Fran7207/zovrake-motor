"""Almacén en memoria de catálogos de modelos definitivos del CMB."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    DefinitiveComparativeModelCatalog,
)


class DefinitiveComparativeModelCatalogStore:
    """Persistencia en memoria — sin almacenamiento persistente."""

    def __init__(self) -> None:
        self._catalogs: list[DefinitiveComparativeModelCatalog] = []

    def save(self, catalog: DefinitiveComparativeModelCatalog) -> None:
        self._catalogs.append(catalog)

    def all_catalogs(self) -> tuple[DefinitiveComparativeModelCatalog, ...]:
        return tuple(self._catalogs)

    def count(self) -> int:
        return len(self._catalogs)

    def snapshot(self) -> dict[str, int]:
        return {"catalog_entries_count": self.count()}
