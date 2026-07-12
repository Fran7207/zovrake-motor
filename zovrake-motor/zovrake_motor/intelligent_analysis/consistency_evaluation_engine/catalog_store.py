"""Almacén en memoria de catálogos de evaluación de consistencia."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationCatalog,
)


class ConsistencyEvaluationCatalogStore:
    """Almacén interno de catálogos de consistencia — sin persistencia."""

    def __init__(self) -> None:
        self._entries: dict[str, ConsistencyEvaluationCatalog] = {}

    def save(self, catalog: ConsistencyEvaluationCatalog) -> None:
        self._entries[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> ConsistencyEvaluationCatalog | None:
        return self._entries.get(catalog_id)

    def count(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[str]:
        return list(self._entries.keys())
