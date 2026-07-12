"""Punto de integración preparatorio para Explanation Generation Engine (7.6)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationCatalog,
)
from zovrake_motor.config.categories.intelligent_analysis import ContextEvaluationEngineSettings


class ExplanationGenerationEngineIntegrationPoint:
    """Prepara el consumo del catálogo contextual por el EGE."""

    def __init__(self, *, settings: ContextEvaluationEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_explanation_generation(
        self,
        catalog: ContextEvaluationCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.explanation_generation_engine_prepared,
            "profiles_count": len(catalog.profiles),
            "catalog_id": catalog.catalog_id,
            "status": (
                "prepared"
                if self._settings.explanation_generation_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "explanation_generation_engine_prepared": (
                self._settings.explanation_generation_engine_prepared
            ),
            "integration_status": (
                "prepared"
                if self._settings.explanation_generation_engine_prepared
                else "not_prepared"
            ),
        }
