"""Dynamic Column Builder — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.dynamic_column_builder.engine import DynamicColumnBuilderEngine
from zovrake_motor.comparative_tables.dynamic_column_builder.integration import (
    DynamicColumnMotorIntegration,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeColumnBuildRequest,
    ComparativeColumnBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class DynamicColumnBuilder(ComparativeTablesComponentPort):
    """
    Gestor del Dynamic Column Builder (DCB).

    Responsabilidad única: construir columnas dinámicas de cuadros comparativos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: DynamicColumnBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or DynamicColumnBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "dynamic_column_builder"

    @property
    def component_label(self) -> str:
        return "Dynamic Column Builder"

    @property
    def engine(self) -> DynamicColumnBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: ComparativeColumnBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparativeColumnBuildResult:
        catalog_id = str(request.structure_catalog.get("catalog_id", ""))
        document_id = str(request.structure_catalog.get("document_id", ""))
        model_id = str(request.structure_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = DynamicColumnMotorIntegration.from_comparative_tables_integration(integration)
            bridge.begin_dynamic_column_build(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                structure_catalog_id=catalog_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = DynamicColumnMotorIntegration.from_comparative_tables_integration(integration)
            bridge.complete_dynamic_column_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
