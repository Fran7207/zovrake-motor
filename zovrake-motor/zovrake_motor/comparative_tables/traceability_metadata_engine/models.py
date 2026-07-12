"""Modelos del Traceability & Metadata Engine — enriquecimiento no destructivo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.traceability_metadata_engine.enums import (
    TraceabilityMetadataEnrichmentStatus,
)


@dataclass(frozen=True)
class DocumentEvidenceReference:
    """Referencia a la evidencia documental — sin modificación."""

    document_id: str
    document_representation_id: str
    internal_document_model_id: str
    source_document_reference: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_representation_id": self.document_representation_id,
            "internal_document_model_id": self.internal_document_model_id,
            "source_document_reference": self.source_document_reference,
        }


@dataclass(frozen=True)
class ComparableGroupReference:
    """Referencia al Grupo Comparable — sin modificación."""

    group_id: str
    group_type: str
    table_id: str
    comparative_domain_model_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "group_type": self.group_type,
            "table_id": self.table_id,
            "comparative_domain_model_id": self.comparative_domain_model_id,
        }


@dataclass(frozen=True)
class ProviderTraceabilityReference:
    """Referencia de trazabilidad de un proveedor — preservada."""

    provider_id: str
    organization_id: str
    row_id: str
    document_reference: str
    column_references: tuple[str, ...]
    inherited_context: dict[str, Any]
    confidence_level_available: str
    upstream_traceability: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "organization_id": self.organization_id,
            "row_id": self.row_id,
            "document_reference": self.document_reference,
            "column_references": list(self.column_references),
            "inherited_context": self.inherited_context,
            "confidence_level_available": self.confidence_level_available,
            "upstream_traceability": self.upstream_traceability,
        }


@dataclass(frozen=True)
class ComparativeTableEnrichedTraceability:
    """Trazabilidad consolidada de un Cuadro Comparativo."""

    process_id: UUID
    document_evidence: DocumentEvidenceReference
    comparable_group: ComparableGroupReference
    context_association_id: str
    domain_catalog_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    source_provider_catalog_id: str
    source_integrity_report_id: str
    provider_references: tuple[ProviderTraceabilityReference, ...]
    lineage: dict[str, Any]
    structure_catalog_preserved: bool
    column_catalog_preserved: bool
    row_catalog_preserved: bool
    provider_catalog_preserved: bool
    integrity_report_preserved: bool
    domain_model_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_evidence": self.document_evidence.to_dict(),
            "comparable_group": self.comparable_group.to_dict(),
            "context_association_id": self.context_association_id,
            "domain_catalog_id": self.domain_catalog_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
            "source_provider_catalog_id": self.source_provider_catalog_id,
            "source_integrity_report_id": self.source_integrity_report_id,
            "provider_references": [
                reference.to_dict() for reference in self.provider_references
            ],
            "provider_references_count": len(self.provider_references),
            "lineage": self.lineage,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "integrity_report_preserved": self.integrity_report_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeTableEnrichedMetadata:
    """Metadatos consolidados de un Cuadro Comparativo."""

    internal_identifiers: dict[str, str]
    group_type: str
    model_version: str
    processing_timestamp: str
    processing_status: str
    integrity_status: str
    audit_info: dict[str, Any]
    motor_internal_references: dict[str, str]
    inherited_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "internal_identifiers": self.internal_identifiers,
            "group_type": self.group_type,
            "model_version": self.model_version,
            "processing_timestamp": self.processing_timestamp,
            "processing_status": self.processing_status,
            "integrity_status": self.integrity_status,
            "audit_info": self.audit_info,
            "motor_internal_references": self.motor_internal_references,
            "inherited_metadata": self.inherited_metadata,
        }


@dataclass(frozen=True)
class EnrichedComparativeTable:
    """Cuadro Comparativo enriquecido con trazabilidad y metadatos."""

    enrichment_id: str
    table_id: str
    group_id: str
    group_type: str
    inherited_context: dict[str, Any]
    confidence_level_available: str
    traceability: ComparativeTableEnrichedTraceability
    metadata: ComparativeTableEnrichedMetadata
    column_references: tuple[str, ...]
    row_references: tuple[str, ...]
    provider_references: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "enrichment_id": self.enrichment_id,
            "table_id": self.table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "inherited_context": self.inherited_context,
            "confidence_level_available": self.confidence_level_available,
            "traceability": self.traceability.to_dict(),
            "metadata": self.metadata.to_dict(),
            "column_references": list(self.column_references),
            "row_references": list(self.row_references),
            "provider_references": list(self.provider_references),
        }


@dataclass(frozen=True)
class EnrichedComparativeTableCatalog:
    """Catálogo de cuadros comparativos enriquecidos del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    source_provider_catalog_id: str
    source_integrity_report_id: str
    enriched_tables: tuple[EnrichedComparativeTable, ...]
    comparative_model_builder_prepared: bool = True
    structure_catalog_preserved: bool = True
    column_catalog_preserved: bool = True
    row_catalog_preserved: bool = True
    provider_catalog_preserved: bool = True
    integrity_report_preserved: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
            "source_provider_catalog_id": self.source_provider_catalog_id,
            "source_integrity_report_id": self.source_integrity_report_id,
            "enriched_tables": [table.to_dict() for table in self.enriched_tables],
            "enriched_tables_count": len(self.enriched_tables),
            "comparative_model_builder_prepared": self.comparative_model_builder_prepared,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "integrity_report_preserved": self.integrity_report_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class MetadataEnricherResult:
    """Resultado individual de un enriquecedor."""

    enricher_type: str
    enricher_name: str
    enriched_tables: tuple[EnrichedComparativeTable, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class TraceabilityMetadataEnrichmentRequest:
    """
    Solicitud de enriquecimiento de trazabilidad y metadatos.

    El TME consume exclusivamente catálogos del CSE, DCB, DRB, POE y GIE.
    """

    process_id: UUID
    structure_catalog: dict[str, Any]
    column_catalog: dict[str, Any]
    row_catalog: dict[str, Any]
    provider_catalog: dict[str, Any]
    integrity_report: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TraceabilityMetadataEnrichmentResult:
    """Resultado uniforme del enriquecimiento de trazabilidad y metadatos."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: EnrichedComparativeTableCatalog
    status: TraceabilityMetadataEnrichmentStatus
    enriched_tables_count: int
    structure_catalog_preserved: bool
    column_catalog_preserved: bool
    row_catalog_preserved: bool
    provider_catalog_preserved: bool
    integrity_report_preserved: bool
    domain_model_preserved: bool
    enrichers_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "enriched_tables_count": self.enriched_tables_count,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "integrity_report_preserved": self.integrity_report_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "enrichers_executed": self.enrichers_executed,
            "technical_observations": list(self.technical_observations),
        }
