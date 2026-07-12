"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    DefinitiveComparativeModelCatalog,
)
from zovrake_motor.config.categories.comparative_tables import ComparativeModelBuilderSettings


class ComparativeValidationFrameworkIntegrationPoint:
    """Preparación hacia el Comparative Validation Framework — sin ejecución."""

    def __init__(self, *, settings: ComparativeModelBuilderSettings) -> None:
        self._settings = settings

    def prepare_for_future_validation(
        self,
        catalog: DefinitiveComparativeModelCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.comparative_validation_framework_prepared,
            "models_count": len(catalog.models),
            "catalog_id": catalog.catalog_id,
            "status": (
                "prepared"
                if self._settings.comparative_validation_framework_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "comparative_validation_framework_prepared": (
                self._settings.comparative_validation_framework_prepared
            ),
            "status": (
                "prepared"
                if self._settings.comparative_validation_framework_prepared
                else "not_prepared"
            ),
        }
