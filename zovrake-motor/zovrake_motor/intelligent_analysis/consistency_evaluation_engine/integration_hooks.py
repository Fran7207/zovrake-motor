"""Punto de integración preparatorio para Risk Analysis Engine (7.4)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationCatalog,
)
from zovrake_motor.config.categories.intelligent_analysis import ConsistencyEvaluationEngineSettings


class RiskAnalysisEngineIntegrationPoint:
    """Prepara el consumo del catálogo de consistencia por el RAE."""

    def __init__(self, *, settings: ConsistencyEvaluationEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_risk_analysis(
        self,
        catalog: ConsistencyEvaluationCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.risk_analysis_engine_prepared,
            "profiles_count": len(catalog.profiles),
            "catalog_id": catalog.catalog_id,
            "status": (
                "prepared"
                if self._settings.risk_analysis_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "risk_analysis_engine_prepared": self._settings.risk_analysis_engine_prepared,
            "integration_status": (
                "prepared"
                if self._settings.risk_analysis_engine_prepared
                else "not_prepared"
            ),
        }
