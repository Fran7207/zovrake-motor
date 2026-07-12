"""Punto de integración del RGE con el Reasoning Result Builder (7.8)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationCatalog,
)
from zovrake_motor.config.categories.intelligent_analysis import RecommendationGenerationEngineSettings


class ReasoningResultBuilderIntegrationPoint:
    """Prepara el catálogo de recomendaciones para consumo futuro por el RRB."""

    def __init__(self, *, settings: RecommendationGenerationEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_result_building(
        self,
        catalog: RecommendationGenerationCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.reasoning_result_builder_prepared,
            "catalog_id": catalog.catalog_id,
            "profiles_count": len(catalog.profiles),
            "status": (
                "ready_for_reasoning_result_building"
                if self._settings.reasoning_result_builder_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "reasoning_result_builder_prepared": self._settings.reasoning_result_builder_prepared,
            "integration_mode": "downstream_preparation",
            "status": (
                "ready_for_reasoning_result_building"
                if self._settings.reasoning_result_builder_prepared
                else "not_prepared"
            ),
        }
