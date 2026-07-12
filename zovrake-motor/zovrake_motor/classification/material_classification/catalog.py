"""Catálogo en memoria de materiales clasificados."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.classification.material_classification.models import MaterialCatalog


class MaterialCatalogStore:
    """
    Almacén temporal del catálogo de materiales.

    Sin persistencia — preparado para consultas futuras dentro del proceso.
    """

    def __init__(self) -> None:
        self._catalogs: dict[str, MaterialCatalog] = {}

    def save(self, catalog: MaterialCatalog) -> None:
        self._catalogs[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> MaterialCatalog | None:
        return self._catalogs.get(catalog_id)

    def get_by_process(self, process_id: UUID) -> MaterialCatalog | None:
        for catalog in self._catalogs.values():
            if catalog.process_id == process_id:
                return catalog
        return None

    def count(self) -> int:
        return len(self._catalogs)

    def snapshot(self) -> list[dict[str, Any]]:
        return [catalog.to_dict() for catalog in self._catalogs.values()]
