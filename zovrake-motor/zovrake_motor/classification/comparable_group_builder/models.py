"""Modelos del Comparable Group Builder y catálogo de grupos comparables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.comparable_group_builder.enums import ComparableGroupBuildStatus


@dataclass(frozen=True)
class ComparableGroupCommercialInformation:
    """Información comercial asociada al grupo."""

    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"fields": self.fields}


@dataclass(frozen=True)
class ComparableGroupTechnicalInformation:
    """Información técnica asociada al grupo."""

    specifications: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "specifications": list(self.specifications),
            "fields": self.fields,
        }


@dataclass(frozen=True)
class ComparableGroupModelReference:
    """Referencias al Modelo Documental Interno."""

    model_id: str
    document_id: str
    concept_ids: tuple[str, ...]
    normalized_concept_ids: tuple[str, ...]
    document_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "document_id": self.document_id,
            "concept_ids": list(self.concept_ids),
            "normalized_concept_ids": list(self.normalized_concept_ids),
            "document_ids": list(self.document_ids),
        }


@dataclass(frozen=True)
class ComparableGroupTraceability:
    """Trazabilidad completa del grupo comparable."""

    process_id: UUID
    document_id: str
    model_id: str
    source_equivalence_catalog_id: str
    source_normalized_catalog_id: str
    equivalence_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    normalized_concept_ids: tuple[str, ...]
    document_reference: str
    canonical_reference: str
    original_preserved: bool
    document_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "document_ids": list(self.document_ids),
            "model_id": self.model_id,
            "source_equivalence_catalog_id": self.source_equivalence_catalog_id,
            "source_normalized_catalog_id": self.source_normalized_catalog_id,
            "equivalence_ids": list(self.equivalence_ids),
            "concept_ids": list(self.concept_ids),
            "normalized_concept_ids": list(self.normalized_concept_ids),
            "document_reference": self.document_reference,
            "canonical_reference": self.canonical_reference,
            "original_preserved": self.original_preserved,
        }


@dataclass(frozen=True)
class ComparableGroupRecord:
    """Registro uniforme de un Grupo Comparable."""

    group_id: str
    internal_group_id: str
    group_type: str
    normalized_concept_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    equivalence_ids: tuple[str, ...]
    provider_references: tuple[str, ...]
    commercial_information: ComparableGroupCommercialInformation
    technical_information: ComparableGroupTechnicalInformation
    model_reference: ComparableGroupModelReference
    traceability: ComparableGroupTraceability
    status: ComparableGroupBuildStatus = ComparableGroupBuildStatus.BUILT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "internal_group_id": self.internal_group_id,
            "group_type": self.group_type,
            "normalized_concept_ids": list(self.normalized_concept_ids),
            "concept_ids": list(self.concept_ids),
            "equivalence_ids": list(self.equivalence_ids),
            "provider_references": list(self.provider_references),
            "commercial_information": self.commercial_information.to_dict(),
            "technical_information": self.technical_information.to_dict(),
            "model_reference": self.model_reference.to_dict(),
            "traceability": self.traceability.to_dict(),
            "status": self.status.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparableGroupCatalog:
    """Catálogo uniforme de grupos comparables."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_equivalence_catalog_id: str
    groups: tuple[ComparableGroupRecord, ...]
    document_ids: tuple[str, ...] = ()
    context_association_prepared: bool = True
    comparative_domain_model_prepared: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "document_ids": list(self.document_ids),
            "source_equivalence_catalog_id": self.source_equivalence_catalog_id,
            "groups": [group.to_dict() for group in self.groups],
            "groups_count": len(self.groups),
            "context_association_prepared": self.context_association_prepared,
            "comparative_domain_model_prepared": self.comparative_domain_model_prepared,
        }


@dataclass(frozen=True)
class ComparableGroupBuildIncident:
    """Incidencia detectada durante la construcción de grupos."""

    builder_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class GroupBuilderResult:
    """Resultado individual de un constructor de grupos."""

    builder_type: str
    builder_name: str
    groups: tuple[ComparableGroupRecord, ...] = ()
    incidents: tuple[ComparableGroupBuildIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparableGroupBuildRequest:
    """
    Solicitud de construcción de grupos comparables.

    El CGB consume exclusivamente el catálogo del EDE.
    """

    process_id: UUID
    equivalence_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparableGroupBuildResult:
    """Resultado uniforme de la construcción de grupos comparables."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ComparableGroupCatalog
    status: ComparableGroupBuildStatus
    incidents: tuple[ComparableGroupBuildIncident, ...]
    equivalence_catalog_preserved: bool
    builders_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "equivalence_catalog_preserved": self.equivalence_catalog_preserved,
            "builders_executed": self.builders_executed,
            "technical_observations": list(self.technical_observations),
        }