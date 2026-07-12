"""Modelos del Context Integration Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.context_integration.enums import ContextIncidentSeverity, ContextIntegrationStatus
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildResult
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexResult


@dataclass(frozen=True)
class RequirementContextModel:
    """
    Modelo uniforme del contexto del requerimiento.

    Representa exclusivamente la información de 'Detalles del requerimiento'
    sin interpretar su contenido.
    """

    context_id: str
    description: str
    observations: tuple[str, ...]
    priorities: tuple[str, ...]
    restrictions: tuple[str, ...]
    additional_notes: tuple[str, ...]
    metadata: dict[str, Any]
    immutable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "description": self.description,
            "observations": list(self.observations),
            "priorities": list(self.priorities),
            "restrictions": list(self.restrictions),
            "additional_notes": list(self.additional_notes),
            "metadata": self.metadata,
            "immutable": self.immutable,
        }


@dataclass(frozen=True)
class ContextTraceability:
    """
    Trazabilidad completa del contexto integrado.

    Mantiene vínculos con documento original, representación canónica,
    modelo interno, índice documental y contexto asociado.
    """

    context_id: str
    process_id: UUID
    document_id: str
    model_id: str
    index_id: str
    canonical_reference_id: str
    extraction_reference_id: str
    document_reference: str
    requirement_code: str
    original_preserved: bool
    document_unmodified: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "index_id": self.index_id,
            "canonical_reference_id": self.canonical_reference_id,
            "extraction_reference_id": self.extraction_reference_id,
            "document_reference": self.document_reference,
            "requirement_code": self.requirement_code,
            "original_preserved": self.original_preserved,
            "document_unmodified": self.document_unmodified,
        }


@dataclass(frozen=True)
class ContextAssociation:
    """
    Asociación uniforme entre contexto y modelo documental.

    Cada asociación representa un único vínculo proceso-documento-contexto.
    """

    association_id: str
    traceability: ContextTraceability
    context: RequirementContextModel
    status: ContextIntegrationStatus
    model_reference: str
    index_reference: str
    classification_prepared: bool
    reasoning_prepared: bool
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "association_id": self.association_id,
            "traceability": self.traceability.to_dict(),
            "context": self.context.to_dict(),
            "status": self.status.value,
            "model_reference": self.model_reference,
            "index_reference": self.index_reference,
            "classification_prepared": self.classification_prepared,
            "reasoning_prepared": self.reasoning_prepared,
            "technical_observations": list(self.technical_observations),
        }


@dataclass(frozen=True)
class ContextIntegrationIncident:
    """Incidencia detectada durante la integración de contexto."""

    message: str
    severity: ContextIncidentSeverity = ContextIncidentSeverity.INFO

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class ContextIntegrationRequest:
    """
    Solicitud de integración de contexto.

    El CIE recibe exclusivamente 'Detalles del requerimiento' como fuente
    de contexto, junto con el modelo interno y el resultado de indexación.
    """

    process_id: UUID
    detalles_requerimiento: str
    index_result: DocumentIndexResult
    model_result: InternalModelBuildResult
    requirement_code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextIntegrationResult:
    """Resultado uniforme de la integración de contexto."""

    process_id: UUID
    document_id: str
    context_id: str
    association: ContextAssociation
    incidents: tuple[ContextIntegrationIncident, ...]
    document_unmodified: bool
    original_preserved: bool
    associations_count: int
    technical_observations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "context_id": self.context_id,
            "association": self.association.to_dict(),
            "incidents": [incident.to_dict() for incident in self.incidents],
            "document_unmodified": self.document_unmodified,
            "original_preserved": self.original_preserved,
            "associations_count": self.associations_count,
            "technical_observations": list(self.technical_observations),
        }
