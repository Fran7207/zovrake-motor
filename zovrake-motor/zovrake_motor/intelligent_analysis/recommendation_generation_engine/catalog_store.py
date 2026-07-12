"""Almacén en memoria de catálogos de recomendaciones."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationCatalog,
)


class RecommendationGenerationCatalogStore:
    """Almacén interno de catálogos de recomendaciones — sin persistencia."""

    def __init__(self) -> None:
        self._entries: dict[str, RecommendationGenerationCatalog] = {}

    def save(self, catalog: RecommendationGenerationCatalog) -> None:
        self._entries[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> RecommendationGenerationCatalog | None:
        return self._entries.get(catalog_id)

    def count(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[str]:
        return list(self._entries.keys())
