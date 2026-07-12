"""Puntos de integración del EGE con motores posteriores."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationCatalog,
)
from zovrake_motor.config.categories.intelligent_analysis import ExplanationGenerationEngineSettings


class ConclusionGenerationEngineIntegrationPoint:
    """Prepara el catálogo de explicaciones para consumo futuro por el CGE."""

    def __init__(self, *, settings: ExplanationGenerationEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_conclusion_generation(
        self,
        catalog: ExplanationGenerationCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.conclusion_generation_engine_prepared,
            "catalog_id": catalog.catalog_id,
            "profiles_count": len(catalog.profiles),
            "status": (
                "ready_for_conclusion_generation"
                if self._settings.conclusion_generation_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "conclusion_generation_engine_prepared": (
                self._settings.conclusion_generation_engine_prepared
            ),
            "integration_mode": "downstream_preparation",
            "status": (
                "ready_for_conclusion_generation"
                if self._settings.conclusion_generation_engine_prepared
                else "not_prepared"
            ),
        }


class RecommendationGenerationEngineIntegrationPoint:
    """Prepara el catálogo de explicaciones para consumo futuro por el RGE."""

    def __init__(self, *, settings: ExplanationGenerationEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_recommendation_generation(
        self,
        catalog: ExplanationGenerationCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.recommendation_generation_engine_prepared,
            "catalog_id": catalog.catalog_id,
            "profiles_count": len(catalog.profiles),
            "status": (
                "ready_for_recommendation_generation"
                if self._settings.recommendation_generation_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "recommendation_generation_engine_prepared": (
                self._settings.recommendation_generation_engine_prepared
            ),
            "integration_mode": "downstream_preparation",
            "status": (
                "ready_for_recommendation_generation"
                if self._settings.recommendation_generation_engine_prepared
                else "not_prepared"
            ),
        }
