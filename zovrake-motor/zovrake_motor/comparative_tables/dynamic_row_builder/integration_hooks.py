"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.dynamic_row_builder.models import ComparativeTableRowCatalog
from zovrake_motor.config.categories.comparative_tables import DynamicRowBuilderSettings


class ProviderOrganizationEngineIntegrationPoint:
    """Preparación hacia el Provider Organization Engine — sin ejecución."""

    def __init__(self, *, settings: DynamicRowBuilderSettings) -> None:
        self._settings = settings

    def prepare_for_future_organization(
        self,
        catalog: ComparativeTableRowCatalog,
    ) -> dict[str, Any]:
        total_rows = sum(len(row_set.rows) for row_set in catalog.row_sets)
        return {
            "prepared": self._settings.provider_organization_engine_prepared,
            "row_sets_count": len(catalog.row_sets),
            "rows_count": total_rows,
            "status": (
                "prepared"
                if self._settings.provider_organization_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "provider_organization_engine_prepared": (
                self._settings.provider_organization_engine_prepared
            ),
            "status": (
                "prepared"
                if self._settings.provider_organization_engine_prepared
                else "not_prepared"
            ),
        }
