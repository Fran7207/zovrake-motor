"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.dynamic_column_builder.models import ComparativeTableColumnCatalog
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings


class DynamicRowBuilderIntegrationPoint:
    """Preparación hacia el Dynamic Row Builder — sin ejecución."""

    def __init__(self, *, settings: DynamicColumnBuilderSettings) -> None:
        self._settings = settings

    def prepare_for_future_rows(
        self,
        catalog: ComparativeTableColumnCatalog,
    ) -> dict[str, Any]:
        total_columns = sum(len(column_set.columns) for column_set in catalog.column_sets)
        return {
            "prepared": self._settings.dynamic_row_builder_prepared,
            "column_sets_count": len(catalog.column_sets),
            "columns_count": total_columns,
            "status": "prepared" if self._settings.dynamic_row_builder_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "dynamic_row_builder_prepared": self._settings.dynamic_row_builder_prepared,
            "status": "prepared" if self._settings.dynamic_row_builder_prepared else "not_prepared",
        }
