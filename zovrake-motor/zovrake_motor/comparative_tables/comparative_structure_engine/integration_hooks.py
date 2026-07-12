"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeTableStructureCatalog,
)
from zovrake_motor.config.categories.comparative_tables import ComparativeStructureEngineSettings


class DynamicColumnBuilderIntegrationPoint:
    """Preparación hacia el Dynamic Column Builder — sin ejecución."""

    def __init__(self, *, settings: ComparativeStructureEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_columns(
        self,
        catalog: ComparativeTableStructureCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.dynamic_column_builder_prepared,
            "structures_count": len(catalog.structures),
            "status": "prepared" if self._settings.dynamic_column_builder_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "dynamic_column_builder_prepared": self._settings.dynamic_column_builder_prepared,
            "status": "prepared" if self._settings.dynamic_column_builder_prepared else "not_prepared",
        }


class DynamicRowBuilderIntegrationPoint:
    """Preparación hacia el Dynamic Row Builder — sin ejecución."""

    def __init__(self, *, settings: ComparativeStructureEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_rows(
        self,
        catalog: ComparativeTableStructureCatalog,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.dynamic_row_builder_prepared,
            "structures_count": len(catalog.structures),
            "status": "prepared" if self._settings.dynamic_row_builder_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "dynamic_row_builder_prepared": self._settings.dynamic_row_builder_prepared,
            "status": "prepared" if self._settings.dynamic_row_builder_prepared else "not_prepared",
        }
