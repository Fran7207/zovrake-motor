"""Punto de integración preparatorio para Consistency Evaluation Engine (7.3)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import EvidenceAnalysisCatalog
from zovrake_motor.config.categories.intelligent_analysis import EvidenceAnalysisEngineSettings


class ConsistencyEvaluationEngineIntegrationPoint:
    """Prepara el consumo del catálogo de evidencias por el CEE."""

    def __init__(self, *, settings: EvidenceAnalysisEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_consistency_evaluation(
        self,
        catalog: EvidenceAnalysisCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.consistency_evaluation_engine_prepared,
            "profiles_count": len(catalog.profiles),
            "catalog_id": catalog.catalog_id,
            "status": (
                "prepared"
                if self._settings.consistency_evaluation_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "consistency_evaluation_engine_prepared": (
                self._settings.consistency_evaluation_engine_prepared
            ),
            "integration_status": (
                "prepared"
                if self._settings.consistency_evaluation_engine_prepared
                else "not_prepared"
            ),
        }
