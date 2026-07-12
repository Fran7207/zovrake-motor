"""Punto de integración preparatorio para Context Evaluation Engine (7.5)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import RiskAnalysisCatalog
from zovrake_motor.config.categories.intelligent_analysis import RiskAnalysisEngineSettings


class ContextEvaluationEngineIntegrationPoint:
    """Prepara el consumo del catálogo de riesgos por el CxEE."""

    def __init__(self, *, settings: RiskAnalysisEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_context_evaluation(
        self,
        catalog: RiskAnalysisCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.context_evaluation_engine_prepared,
            "profiles_count": len(catalog.profiles),
            "catalog_id": catalog.catalog_id,
            "status": (
                "prepared"
                if self._settings.context_evaluation_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "context_evaluation_engine_prepared": (
                self._settings.context_evaluation_engine_prepared
            ),
            "integration_status": (
                "prepared"
                if self._settings.context_evaluation_engine_prepared
                else "not_prepared"
            ),
        }
