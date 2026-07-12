"""Enriquecedores especializados del Traceability & Metadata Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.traceability_metadata_engine.builders import (
    build_enriched_table,
    build_public_enrichment_id,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.enums import (
    MetadataEnricherStrategyType,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.gateway import (
    ColumnSetView,
    MetadataEnrichmentInputView,
    ProviderSetView,
    RowSetView,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    EnrichedComparativeTable,
    MetadataEnricherResult,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.port import MetadataEnricherPort
from zovrake_motor.config.categories.comparative_tables import TraceabilityMetadataEngineSettings


class ComparativeTableMetadataEnricher(MetadataEnricherPort):
    """
    Enriquece cada Cuadro Comparativo con trazabilidad, contexto y metadatos.

    Consolida información del CSE, DCB, DRB, POE y GIE sin modificar orígenes.
    """

    @property
    def enricher_name(self) -> str:
        return "comparative_table_metadata_enricher"

    @property
    def enricher_label(self) -> str:
        return "Enriquecedor de Trazabilidad y Metadatos — Cuadro Comparativo"

    @property
    def enricher_type(self) -> MetadataEnricherStrategyType:
        return MetadataEnricherStrategyType.COMPARATIVE_TABLE

    def enrich(
        self,
        input_view: MetadataEnrichmentInputView,
        *,
        settings: TraceabilityMetadataEngineSettings,
        start_sequence: int,
    ) -> MetadataEnricherResult:
        columns_by_table = {
            column_set.table_id: column_set
            for column_set in input_view.column_catalog.column_sets
        }
        rows_by_table = {
            row_set.table_id: row_set for row_set in input_view.row_catalog.row_sets
        }
        providers_by_table = {
            provider_set.table_id: provider_set
            for provider_set in input_view.provider_catalog.provider_sets
        }
        integrity_by_table = {
            check_set.table_id: check_set.is_valid
            for check_set in input_view.integrity_report.check_sets
        }

        enriched_tables: list[EnrichedComparativeTable] = []
        sequence = start_sequence

        for structure in input_view.structure_catalog.structures:
            enrichment_id = build_public_enrichment_id(
                sequence,
                prefix=settings.enrichment_id_prefix,
                padding=settings.enrichment_id_padding,
            )
            sequence += 1

            enriched_tables.append(
                build_enriched_table(
                    structure=structure,
                    column_set=columns_by_table.get(structure.table_id),
                    row_set=rows_by_table.get(structure.table_id),
                    provider_set=providers_by_table.get(structure.table_id),
                    input_view=input_view,
                    enrichment_id=enrichment_id,
                    integrity_valid=integrity_by_table.get(structure.table_id, True),
                    enricher_name=self.enricher_name,
                    settings=settings,
                ),
            )

        return MetadataEnricherResult(
            enricher_type=self.enricher_type.value,
            enricher_name=self.enricher_name,
            enriched_tables=tuple(enriched_tables),
            technical_observations=(
                f"enricher_type={self.enricher_type.value}",
                f"enriched_tables_count={len(enriched_tables)}",
                f"structures_evaluated={len(input_view.structure_catalog.structures)}",
            ),
        )
