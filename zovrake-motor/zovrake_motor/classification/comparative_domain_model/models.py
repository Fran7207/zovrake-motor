"""Modelos del Comparative Domain Model Builder — contrato oficial PM5 → PM6."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.comparative_domain_model.enums import ComparativeDomainModelBuildStatus


@dataclass(frozen=True)
class ComparativeDomainCommercialInformation:
    """Información comercial del modelo comparativo."""

    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"fields": self.fields}


@dataclass(frozen=True)
class ComparativeDomainTechnicalInformation:
    """Información técnica del modelo comparativo."""

    specifications: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "specifications": list(self.specifications),
            "fields": self.fields,
        }


@dataclass(frozen=True)
class ComparativeDomainContextReference:
    """Referencia al contexto relacionado — preservado sin modificación."""

    context_id: str
    description: str
    association_id: str
    codigo_req: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "description": self.description,
            "association_id": self.association_id,
            "codigo_req": self.codigo_req,
        }


@dataclass(frozen=True)
class ComparativeDomainTraceability:
    """Trazabilidad completa del modelo comparativo."""

    process_id: UUID
    document_id: str
    model_id: str
    source_context_association_catalog_id: str
    source_comparable_group_catalog_id: str
    group_id: str
    association_id: str
    equivalence_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    normalized_concept_ids: tuple[str, ...]
    document_reference: str
    canonical_reference: str
    original_preserved: bool
    context_preserved: bool
    document_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "document_ids": list(self.document_ids),
            "model_id": self.model_id,
            "source_context_association_catalog_id": self.source_context_association_catalog_id,
            "source_comparable_group_catalog_id": self.source_comparable_group_catalog_id,
            "group_id": self.group_id,
            "association_id": self.association_id,
            "equivalence_ids": list(self.equivalence_ids),
            "concept_ids": list(self.concept_ids),
            "normalized_concept_ids": list(self.normalized_concept_ids),
            "document_reference": self.document_reference,
            "canonical_reference": self.canonical_reference,
            "original_preserved": self.original_preserved,
            "context_preserved": self.context_preserved,
        }


@dataclass(frozen=True)
class ComparativeDomainModelRecord:
    """
    Modelo Comparativo de Dominio — un registro por Grupo Comparable.

    Contrato oficial consumido por el Prompt Maestro 6.
    """

    comparative_model_id: str
    internal_model_id: str
    group_id: str
    group_type: str
    primary_item: str
    equivalent_concepts: tuple[str, ...]
    providers: tuple[str, ...]
    commercial_information: ComparativeDomainCommercialInformation
    technical_information: ComparativeDomainTechnicalInformation
    related_context: ComparativeDomainContextReference
    confidence_level_available: str
    traceability: ComparativeDomainTraceability
    status: ComparativeDomainModelBuildStatus = ComparativeDomainModelBuildStatus.BUILT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparative_model_id": self.comparative_model_id,
            "internal_model_id": self.internal_model_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "primary_item": self.primary_item,
            "equivalent_concepts": list(self.equivalent_concepts),
            "providers": list(self.providers),
            "commercial_information": self.commercial_information.to_dict(),
            "technical_information": self.technical_information.to_dict(),
            "related_context": self.related_context.to_dict(),
            "confidence_level_available": self.confidence_level_available,
            "traceability": self.traceability.to_dict(),
            "status": self.status.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparativeDomainModelCatalog:
    """
    Catálogo del Modelo Comparativo de Dominio.

    Salida oficial del Prompt Maestro 5 — entrada oficial del Prompt Maestro 6.
    """

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_context_association_catalog_id: str
    models: tuple[ComparativeDomainModelRecord, ...]
    document_ids: tuple[str, ...] = ()
    pm6_output_contract: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "document_ids": list(self.document_ids),
            "source_context_association_catalog_id": self.source_context_association_catalog_id,
            "models": [model.to_dict() for model in self.models],
            "models_count": len(self.models),
            "pm6_output_contract": self.pm6_output_contract,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class ComparativeDomainModelBuildIncident:
    """Incidencia detectada durante la construcción del modelo comparativo."""

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
class DomainModelBuilderResult:
    """Resultado individual de un constructor de modelo comparativo."""

    builder_type: str
    builder_name: str
    models: tuple[ComparativeDomainModelRecord, ...] = ()
    incidents: tuple[ComparativeDomainModelBuildIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparativeDomainModelBuildRequest:
    """
    Solicitud de construcción del Modelo Comparativo de Dominio.

    El CDMB consume exclusivamente el catálogo del CAE-Context.
    """

    process_id: UUID
    context_association_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeDomainModelBuildResult:
    """Resultado uniforme de la construcción del modelo comparativo."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ComparativeDomainModelCatalog
    status: ComparativeDomainModelBuildStatus
    incidents: tuple[ComparativeDomainModelBuildIncident, ...]
    source_data_preserved: bool
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
            "source_data_preserved": self.source_data_preserved,
            "builders_executed": self.builders_executed,
            "technical_observations": list(self.technical_observations),
        }