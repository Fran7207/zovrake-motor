"""Almacén en memoria de catálogos de resultados del análisis inteligente."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    IntelligentAnalysisResultCatalog,
)


class ReasoningResultCatalogStore:
    """Almacén interno de catálogos de resultados — sin persistencia."""

    def __init__(self) -> None:
        self._entries: dict[str, IntelligentAnalysisResultCatalog] = {}

    def save(self, catalog: IntelligentAnalysisResultCatalog) -> None:
        self._entries[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> IntelligentAnalysisResultCatalog | None:
        return self._entries.get(catalog_id)

    def get_by_process(self, process_id: UUID) -> tuple[IntelligentAnalysisResultCatalog, ...]:
        return tuple(
            catalog
            for catalog in self._entries.values()
            if str(catalog.process_id) == str(process_id)
        )

    def count(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[str]:
        return list(self._entries.keys())
