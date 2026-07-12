"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    EnrichedComparativeTableCatalog,
)
from zovrake_motor.config.categories.comparative_tables import TraceabilityMetadataEngineSettings


class ComparativeModelBuilderIntegrationPoint:
    """Preparación hacia el Comparative Model Builder — sin ejecución."""

    def __init__(self, *, settings: TraceabilityMetadataEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_model_build(
        self,
        catalog: EnrichedComparativeTableCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.comparative_model_builder_prepared,
            "enriched_tables_count": len(catalog.enriched_tables),
            "catalog_id": catalog.catalog_id,
            "status": (
                "prepared"
                if self._settings.comparative_model_builder_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "comparative_model_builder_prepared": self._settings.comparative_model_builder_prepared,
            "status": (
                "prepared"
                if self._settings.comparative_model_builder_prepared
                else "not_prepared"
            ),
        }
