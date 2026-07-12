"""Almacén en memoria de catálogos de explicaciones."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationCatalog,
)


class ExplanationGenerationCatalogStore:
    """Almacén interno de catálogos de explicaciones — sin persistencia."""

    def __init__(self) -> None:
        self._entries: dict[str, ExplanationGenerationCatalog] = {}

    def save(self, catalog: ExplanationGenerationCatalog) -> None:
        self._entries[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> ExplanationGenerationCatalog | None:
        return self._entries.get(catalog_id)

    def count(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[str]:
        return list(self._entries.keys())
