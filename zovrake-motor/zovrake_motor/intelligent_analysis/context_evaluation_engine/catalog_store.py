"""Almacén en memoria de catálogos de evaluación contextual."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import ContextEvaluationCatalog


class ContextEvaluationCatalogStore:
    """Almacén interno de catálogos contextuales — sin persistencia."""

    def __init__(self) -> None:
        self._entries: dict[str, ContextEvaluationCatalog] = {}

    def save(self, catalog: ContextEvaluationCatalog) -> None:
        self._entries[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> ContextEvaluationCatalog | None:
        return self._entries.get(catalog_id)

    def count(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[str]:
        return list(self._entries.keys())
