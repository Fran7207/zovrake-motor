"""Dynamic Row Builder — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.dynamic_row_builder.engine import DynamicRowBuilderEngine
from zovrake_motor.comparative_tables.dynamic_row_builder.integration import (
    DynamicRowMotorIntegration,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildRequest,
    ComparativeRowBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class DynamicRowBuilder(ComparativeTablesComponentPort):
    """
    Gestor del Dynamic Row Builder (DRB).

    Responsabilidad única: construir filas dinámicas de cuadros comparativos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: DynamicRowBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or DynamicRowBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "dynamic_row_builder"

    @property
    def component_label(self) -> str:
        return "Dynamic Row Builder"

    @property
    def engine(self) -> DynamicRowBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: ComparativeRowBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparativeRowBuildResult:
        column_catalog_id = str(request.column_catalog.get("catalog_id", ""))
        structure_catalog_id = str(request.structure_catalog.get("catalog_id", ""))
        document_id = str(request.column_catalog.get("document_id", ""))
        model_id = str(request.column_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = DynamicRowMotorIntegration.from_comparative_tables_integration(integration)
            bridge.begin_dynamic_row_build(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                column_catalog_id=column_catalog_id,
                structure_catalog_id=structure_catalog_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = DynamicRowMotorIntegration.from_comparative_tables_integration(integration)
            bridge.complete_dynamic_row_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
