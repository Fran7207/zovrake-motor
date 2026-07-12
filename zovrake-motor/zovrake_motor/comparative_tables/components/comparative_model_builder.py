"""Comparative Model Builder — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.comparative_model_builder.engine import (
    ComparativeModelBuilderEngine,
)
from zovrake_motor.comparative_tables.comparative_model_builder.integration import (
    ComparativeModelMotorIntegration,
)
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildRequest,
    ComparativeModelBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeModelBuilder(ComparativeTablesComponentPort):
    """
    Gestor del Comparative Model Builder (CMB).

    Responsabilidad única: construir el Modelo Comparativo Definitivo.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ComparativeModelBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ComparativeModelBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "comparative_model_builder"

    @property
    def component_label(self) -> str:
        return "Comparative Model Builder"

    @property
    def engine(self) -> ComparativeModelBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: ComparativeModelBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparativeModelBuildResult:
        enriched_catalog_id = str(request.enriched_catalog.get("catalog_id", ""))
        document_id = str(request.enriched_catalog.get("document_id", ""))
        model_id = str(request.enriched_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ComparativeModelMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.begin_comparative_model_build(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                enriched_catalog_id=enriched_catalog_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = ComparativeModelMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.complete_comparative_model_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
