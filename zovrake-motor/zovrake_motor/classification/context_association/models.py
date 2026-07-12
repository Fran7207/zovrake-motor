"""Modelos del Context Association Engine y catálogo de asociaciones."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.context_association.enums import ContextAssociationStatus


@dataclass(frozen=True)
class PreservedIntegratedContext:
    """
    Contexto integrado preservado sin modificación.

    Representa exclusivamente el campo 'Detalles del requerimiento'.
    """

    context_id: str
    description: str
    process_id: UUID
    codigo_req: str = ""
    observations: tuple[str, ...] = ()
    priorities: tuple[str, ...] = ()
    restrictions: tuple[str, ...] = ()
    additional_notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    immutable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "description": self.description,
            "process_id": str(self.process_id),
            "codigo_req": self.codigo_req,
            "observations": list(self.observations),
            "priorities": list(self.priorities),
            "restrictions": list(self.restrictions),
            "additional_notes": list(self.additional_notes),
            "metadata": self.metadata,
            "immutable": self.immutable,
        }


@dataclass(frozen=True)
class ContextAssociationTraceability:
    """Trazabilidad completa de una asociación contexto-grupo."""

    process_id: UUID
    document_id: str
    model_id: str
    source_comparable_group_catalog_id: str
    group_id: str
    internal_group_id: str
    context_id: str
    equivalence_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    normalized_concept_ids: tuple[str, ...]
    document_reference: str
    canonical_reference: str
    original_preserved: bool
    context_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "source_comparable_group_catalog_id": self.source_comparable_group_catalog_id,
            "group_id": self.group_id,
            "internal_group_id": self.internal_group_id,
            "context_id": self.context_id,
            "equivalence_ids": list(self.equivalence_ids),
            "concept_ids": list(self.concept_ids),
            "normalized_concept_ids": list(self.normalized_concept_ids),
            "document_reference": self.document_reference,
            "canonical_reference": self.canonical_reference,
            "original_preserved": self.original_preserved,
            "context_preserved": self.context_preserved,
        }


@dataclass(frozen=True)
class ContextAssociationRecord:
    """Relación uniforme entre un Grupo Comparable y el contexto del requerimiento."""

    association_id: str
    group_id: str
    internal_group_id: str
    context_id: str
    traceability: ContextAssociationTraceability
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "association_id": self.association_id,
            "group_id": self.group_id,
            "internal_group_id": self.internal_group_id,
            "context_id": self.context_id,
            "traceability": self.traceability.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ContextAssociationCatalog:
    """Catálogo uniforme de asociaciones contexto-grupo."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_comparable_group_catalog_id: str
    preserved_context: PreservedIntegratedContext
    preserved_groups: tuple[dict[str, Any], ...]
    associations: tuple[ContextAssociationRecord, ...]
    comparable_group_catalog_preserved: bool = True
    context_preserved: bool = True
    comparative_domain_model_prepared: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_comparable_group_catalog_id": self.source_comparable_group_catalog_id,
            "preserved_context": self.preserved_context.to_dict(),
            "preserved_groups": list(self.preserved_groups),
            "associations": [association.to_dict() for association in self.associations],
            "associations_count": len(self.associations),
            "comparable_group_catalog_preserved": self.comparable_group_catalog_preserved,
            "context_preserved": self.context_preserved,
            "comparative_domain_model_prepared": self.comparative_domain_model_prepared,
        }


@dataclass(frozen=True)
class ContextAssociationIncident:
    """Incidencia detectada durante la asociación de contexto."""

    associator_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "associator_name": self.associator_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ContextAssociatorResult:
    """Resultado individual de un asociador de contexto."""

    associator_type: str
    associator_name: str
    associations: tuple[ContextAssociationRecord, ...] = ()
    incidents: tuple[ContextAssociationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextAssociationRequest:
    """
    Solicitud de asociación de contexto.

    El CAE-Context consume exclusivamente el catálogo del CGB y el contexto integrado.
    """

    process_id: UUID
    comparable_group_catalog: dict[str, Any]
    integrated_context: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextAssociationResult:
    """Resultado uniforme de la asociación de contexto."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ContextAssociationCatalog
    status: ContextAssociationStatus
    incidents: tuple[ContextAssociationIncident, ...]
    comparable_group_catalog_preserved: bool
    context_preserved: bool
    associators_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "comparable_group_catalog_preserved": self.comparable_group_catalog_preserved,
            "context_preserved": self.context_preserved,
            "associators_executed": self.associators_executed,
            "technical_observations": list(self.technical_observations),
        }
