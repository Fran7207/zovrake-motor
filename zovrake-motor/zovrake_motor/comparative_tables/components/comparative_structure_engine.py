"""Comparative Structure Engine — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.comparative_structure_engine.engine import (
    ComparativeStructureBuilderEngine,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.integration import (
    ComparativeStructureMotorIntegration,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildRequest,
    ComparativeStructureBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeStructureEngine(ComparativeTablesComponentPort):
    """
    Gestor del Comparative Structure Engine (CSE).

    Responsabilidad única: construir la estructura base de cada Cuadro Comparativo
    a partir del Modelo Comparativo de Dominio.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ComparativeStructureBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ComparativeStructureBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "comparative_structure_engine"

    @property
    def component_label(self) -> str:
        return "Comparative Structure Engine"

    @property
    def engine(self) -> ComparativeStructureBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: ComparativeStructureBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparativeStructureBuildResult:
        catalog_id = str(request.domain_model_catalog.get("catalog_id", ""))
        document_id = str(request.domain_model_catalog.get("document_id", ""))
        model_id = str(request.domain_model_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ComparativeStructureMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.begin_comparative_structure_build(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                domain_catalog_id=catalog_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = ComparativeStructureMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.complete_comparative_structure_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
