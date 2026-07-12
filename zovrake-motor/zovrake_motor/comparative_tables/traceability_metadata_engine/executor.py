"""Ejecutor de enriquecedores del Traceability & Metadata Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.traceability_metadata_engine.builders import (
    build_enriched_catalog,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.enums import (
    TraceabilityMetadataEnrichmentStatus,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.gateway import (
    MetadataEnrichmentInputView,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    EnrichedComparativeTable,
    TraceabilityMetadataEnrichmentResult,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.registry import (
    MetadataEnricherRegistry,
)
from zovrake_motor.config.categories.comparative_tables import TraceabilityMetadataEngineSettings


class TraceabilityMetadataEnrichmentExecutor:
    """Coordina enriquecedores sin modificar catálogos de entrada."""

    def __init__(self, registry: MetadataEnricherRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: MetadataEnrichmentInputView,
        *,
        settings: TraceabilityMetadataEngineSettings,
    ) -> TraceabilityMetadataEnrichmentResult:
        enriched_tables: list[EnrichedComparativeTable] = []
        observations: list[str] = []
        sequence = 1

        for enricher in self._registry.all_enrichers():
            result = enricher.enrich(
                input_view,
                settings=settings,
                start_sequence=sequence,
            )
            enriched_tables.extend(result.enriched_tables)
            observations.extend(result.technical_observations)
            sequence += len(result.enriched_tables)

        if enriched_tables:
            status = TraceabilityMetadataEnrichmentStatus.ENRICHED
        elif self._registry.count():
            status = TraceabilityMetadataEnrichmentStatus.PARTIAL
        else:
            status = TraceabilityMetadataEnrichmentStatus.SKIPPED

        catalog = build_enriched_catalog(
            input_view=input_view,
            enriched_tables=tuple(enriched_tables),
            settings=settings,
        )

        observations.extend(
            (
                "structure_catalog_preserved=True",
                "column_catalog_preserved=True",
                "row_catalog_preserved=True",
                "provider_catalog_preserved=True",
                "integrity_report_preserved=True",
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "inherited_context_preserved=True",
                "confidence_level_preserved=True",
                "enriched_tables_count=" + str(len(enriched_tables)),
            ),
        )

        return TraceabilityMetadataEnrichmentResult(
            process_id=input_view.structure_catalog.process_id,
            document_id=input_view.structure_catalog.document_id,
            model_id=input_view.structure_catalog.model_id,
            catalog=catalog,
            status=status,
            enriched_tables_count=len(enriched_tables),
            structure_catalog_preserved=True,
            column_catalog_preserved=True,
            row_catalog_preserved=True,
            provider_catalog_preserved=True,
            integrity_report_preserved=True,
            domain_model_preserved=input_view.structure_catalog.domain_model_preserved,
            enrichers_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
