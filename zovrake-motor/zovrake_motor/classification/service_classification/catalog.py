"""Catálogo en memoria de servicios clasificados."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.classification.service_classification.models import ServiceCatalog


class ServiceCatalogStore:
    """
    Almacén temporal del catálogo de servicios.

    Completamente independiente del catálogo de materiales.
    """

    def __init__(self) -> None:
        self._catalogs: dict[str, ServiceCatalog] = {}

    def save(self, catalog: ServiceCatalog) -> None:
        self._catalogs[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> ServiceCatalog | None:
        return self._catalogs.get(catalog_id)

    def get_by_process(self, process_id: UUID) -> ServiceCatalog | None:
        for catalog in self._catalogs.values():
            if catalog.process_id == process_id:
                return catalog
        return None

    def count(self) -> int:
        return len(self._catalogs)

    def snapshot(self) -> list[dict[str, Any]]:
        return [catalog.to_dict() for catalog in self._catalogs.values()]
