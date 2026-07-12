"""Almacén en memoria de catálogos de análisis de riesgos."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import RiskAnalysisCatalog


class RiskAnalysisCatalogStore:
    """Almacén interno de catálogos de riesgos — sin persistencia."""

    def __init__(self) -> None:
        self._entries: dict[str, RiskAnalysisCatalog] = {}

    def save(self, catalog: RiskAnalysisCatalog) -> None:
        self._entries[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> RiskAnalysisCatalog | None:
        return self._entries.get(catalog_id)

    def count(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[str]:
        return list(self._entries.keys())
