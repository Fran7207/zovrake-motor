"""Utilidades de construcción de cuadros comparativos enriquecidos."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from zovrake_motor.comparative_tables.traceability_metadata_engine.gateway import (
    ColumnSetView,
    MetadataEnrichmentInputView,
    ProviderSetView,
    RowSetView,
    StructureView,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    ComparableGroupReference,
    ComparativeTableEnrichedMetadata,
    ComparativeTableEnrichedTraceability,
    DocumentEvidenceReference,
    EnrichedComparativeTable,
    EnrichedComparativeTableCatalog,
    ProviderTraceabilityReference,
)
from zovrake_motor.config.categories.comparative_tables import TraceabilityMetadataEngineSettings


def build_public_enrichment_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def _resolve_processing_timestamp(structure: StructureView) -> str:
    lineage = structure.traceability
    for key in ("processed_at", "processing_timestamp", "created_at", "occurred_at"):
        value = lineage.get(key)
        if value:
            return str(value)
    for key in ("processed_at", "processing_timestamp", "created_at"):
        value = structure.metadata.get(key)
        if value:
            return str(value)
    return ""


def _resolve_model_version(structure: StructureView) -> str:
    for source in (structure.metadata_prepared, structure.metadata, structure.traceability):
        for key in ("model_version", "attribute_snapshot_version", "version"):
            value = source.get(key)
            if value:
                return str(value)
    return "1.0"


def _resolve_document_representation_id(structure: StructureView) -> str:
    lineage = structure.traceability.get("lineage", structure.traceability)
    if isinstance(lineage, dict):
        for key in ("document_representation_id", "canonical_id", "representation_id"):
            value = lineage.get(key)
            if value:
                return str(value)
    return structure.metadata.get("related_context_id", "")


def _build_provider_references(provider_set: ProviderSetView | None) -> tuple[ProviderTraceabilityReference, ...]:
    if provider_set is None:
        return ()
    references: list[ProviderTraceabilityReference] = []
    for provider in provider_set.providers:
        references.append(
            ProviderTraceabilityReference(
                provider_id=provider.provider_id,
                organization_id=provider.organization_id,
                row_id=provider.row_id,
                document_reference=provider.document_reference,
                column_references=provider.column_references,
                inherited_context=dict(provider.inherited_context),
                confidence_level_available=provider.confidence_level_available,
                upstream_traceability=dict(provider.traceability),
            ),
        )
    return tuple(references)


def build_enriched_table(
    *,
    structure: StructureView,
    column_set: ColumnSetView | None,
    row_set: RowSetView | None,
    provider_set: ProviderSetView | None,
    input_view: MetadataEnrichmentInputView,
    enrichment_id: str,
    integrity_valid: bool,
    enricher_name: str,
    settings: TraceabilityMetadataEngineSettings,
) -> EnrichedComparativeTable:
    provider_refs = _build_provider_references(provider_set)
    inherited_context = dict(structure.inherited_context)
    confidence_level = structure.confidence_level_available
    enrichment_recorded_at = datetime.now(timezone.utc).isoformat()

    traceability = ComparativeTableEnrichedTraceability(
        process_id=input_view.structure_catalog.process_id,
        document_evidence=DocumentEvidenceReference(
            document_id=structure.document_id,
            document_representation_id=_resolve_document_representation_id(structure),
            internal_document_model_id=input_view.structure_catalog.model_id,
            source_document_reference=structure.document_id,
        ),
        comparable_group=ComparableGroupReference(
            group_id=structure.group_id,
            group_type=structure.group_type,
            table_id=structure.table_id,
            comparative_domain_model_id=structure.comparative_model_id,
        ),
        context_association_id=str(
            inherited_context.get("context_id", structure.metadata.get("related_context_id", "")),
        ),
        domain_catalog_id=structure.domain_catalog_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
        source_provider_catalog_id=input_view.provider_catalog.catalog_id,
        source_integrity_report_id=input_view.integrity_report.report_id,
        provider_references=provider_refs,
        lineage=dict(structure.traceability),
        structure_catalog_preserved=True,
        column_catalog_preserved=True,
        row_catalog_preserved=True,
        provider_catalog_preserved=True,
        integrity_report_preserved=True,
        domain_model_preserved=input_view.structure_catalog.domain_model_preserved,
    )

    metadata = ComparativeTableEnrichedMetadata(
        internal_identifiers={
            "enrichment_id": enrichment_id,
            "table_id": structure.table_id,
            "internal_table_id": structure.internal_table_id,
            "group_id": structure.group_id,
            "model_id": input_view.structure_catalog.model_id,
            "document_id": structure.document_id,
        },
        group_type=structure.group_type,
        model_version=_resolve_model_version(structure),
        processing_timestamp=_resolve_processing_timestamp(structure),
        processing_status="integrity_valid" if integrity_valid else "integrity_invalid",
        integrity_status="valid" if integrity_valid else "invalid",
        audit_info={
            "enricher_name": enricher_name,
            "enrichment_recorded_at": enrichment_recorded_at,
            "integrity_report_id": input_view.integrity_report.report_id,
            "source_catalogs_preserved": True,
            "inherited_metadata_preserved": True,
        },
        motor_internal_references={
            "structure_catalog_id": input_view.structure_catalog.catalog_id,
            "column_catalog_id": input_view.column_catalog.catalog_id,
            "row_catalog_id": input_view.row_catalog.catalog_id,
            "provider_catalog_id": input_view.provider_catalog.catalog_id,
            "integrity_report_id": input_view.integrity_report.report_id,
        },
        inherited_metadata={
            "structure_metadata": dict(structure.metadata),
            "metadata_prepared": dict(structure.metadata_prepared),
        },
    )

    column_ids = tuple(column.column_id for column in column_set.columns) if column_set else ()
    row_ids = tuple(row.row_id for row in row_set.rows) if row_set else ()
    provider_ids = tuple(provider.provider_id for provider in provider_set.providers) if provider_set else ()

    return EnrichedComparativeTable(
        enrichment_id=enrichment_id,
        table_id=structure.table_id,
        group_id=structure.group_id,
        group_type=structure.group_type,
        inherited_context=inherited_context,
        confidence_level_available=confidence_level,
        traceability=traceability,
        metadata=metadata,
        column_references=column_ids,
        row_references=row_ids,
        provider_references=provider_ids,
    )


def build_enriched_catalog(
    *,
    input_view: MetadataEnrichmentInputView,
    enriched_tables: tuple[EnrichedComparativeTable, ...],
    settings: TraceabilityMetadataEngineSettings,
) -> EnrichedComparativeTableCatalog:
    return EnrichedComparativeTableCatalog(
        catalog_id=f"tme-catalog://{input_view.structure_catalog.model_id}",
        process_id=input_view.structure_catalog.process_id,
        model_id=input_view.structure_catalog.model_id,
        document_id=input_view.structure_catalog.document_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
        source_provider_catalog_id=input_view.provider_catalog.catalog_id,
        source_integrity_report_id=input_view.integrity_report.report_id,
        enriched_tables=enriched_tables,
        comparative_model_builder_prepared=settings.comparative_model_builder_prepared,
        structure_catalog_preserved=True,
        column_catalog_preserved=True,
        row_catalog_preserved=True,
        provider_catalog_preserved=True,
        integrity_report_preserved=True,
        domain_model_preserved=input_view.structure_catalog.domain_model_preserved,
    )
