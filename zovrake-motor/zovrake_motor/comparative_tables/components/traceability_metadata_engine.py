"""Traceability & Metadata Engine — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.traceability_metadata_engine.engine import (
    TraceabilityMetadataEngineCore,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.integration import (
    TraceabilityMetadataMotorIntegration,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    TraceabilityMetadataEnrichmentRequest,
    TraceabilityMetadataEnrichmentResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class TraceabilityMetadataEngine(ComparativeTablesComponentPort):
    """
    Gestor del Traceability & Metadata Engine (TME).

    Responsabilidad única: enriquecer cuadros comparativos con trazabilidad y metadatos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: TraceabilityMetadataEngineCore | None = None,
    ) -> None:
        self._engine = engine or TraceabilityMetadataEngineCore(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "traceability_metadata_engine"

    @property
    def component_label(self) -> str:
        return "Traceability & Metadata Engine"

    @property
    def engine(self) -> TraceabilityMetadataEngineCore:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def enrich(
        self,
        request: TraceabilityMetadataEnrichmentRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> TraceabilityMetadataEnrichmentResult:
        integrity_report_id = str(request.integrity_report.get("report_id", ""))
        document_id = str(request.structure_catalog.get("document_id", ""))
        model_id = str(request.structure_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = TraceabilityMetadataMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.begin_traceability_metadata_enrichment(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                integrity_report_id=integrity_report_id,
            )

        result = self._engine.enrich(request)

        if integration is not None and record_traceability:
            bridge = TraceabilityMetadataMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.complete_traceability_metadata_enrichment(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
