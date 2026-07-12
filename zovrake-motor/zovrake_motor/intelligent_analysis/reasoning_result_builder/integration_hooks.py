"""Punto de integración del RRB con el Integration & Certification Framework (7.9)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    IntelligentAnalysisResultCatalog,
)
from zovrake_motor.config.categories.intelligent_analysis import ReasoningResultBuilderSettings


class IntegrationCertificationFrameworkIntegrationPoint:
    """Prepara el catálogo de resultados para certificación futura."""

    def __init__(self, *, settings: ReasoningResultBuilderSettings) -> None:
        self._settings = settings

    def prepare_for_future_certification(
        self,
        catalog: IntelligentAnalysisResultCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.integration_certification_framework_prepared,
            "catalog_id": catalog.catalog_id,
            "results_count": len(catalog.results),
            "status": (
                "ready_for_integration_certification"
                if self._settings.integration_certification_framework_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_certification_framework_prepared": (
                self._settings.integration_certification_framework_prepared
            ),
            "integration_mode": "downstream_preparation",
            "status": (
                "ready_for_integration_certification"
                if self._settings.integration_certification_framework_prepared
                else "not_prepared"
            ),
        }
