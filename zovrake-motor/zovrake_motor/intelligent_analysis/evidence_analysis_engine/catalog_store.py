"""Almacén en memoria de catálogos de evidencias analizadas."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import EvidenceAnalysisCatalog


class EvidenceAnalysisCatalogStore:
    """Almacén interno de catálogos de evidencias — sin persistencia."""

    def __init__(self) -> None:
        self._entries: dict[str, EvidenceAnalysisCatalog] = {}

    def save(self, catalog: EvidenceAnalysisCatalog) -> None:
        self._entries[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> EvidenceAnalysisCatalog | None:
        return self._entries.get(catalog_id)

    def count(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[str]:
        return list(self._entries.keys())
