"""Modelos del Document Knowledge Index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.internal_model.models import InternalModelBuildResult
from zovrake_motor.comprehension.knowledge_index.enums import IndexEntryStatus, IndexingIncidentSeverity


@dataclass(frozen=True)
class DocumentIndexTraceability:
    """
    Índice de trazabilidad — relación completa del documento procesado.

    Mantiene vínculos con documento original, validación, adaptador,
    representación canónica y modelo documental interno.
    """

    index_id: str
    process_id: UUID
    document_id: str
    model_id: str
    validation_reference: str
    adapter_name: str
    canonical_reference_id: str
    extraction_reference_id: str
    document_reference: str
    original_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "index_id": self.index_id,
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "validation_reference": self.validation_reference,
            "adapter_name": self.adapter_name,
            "canonical_reference_id": self.canonical_reference_id,
            "extraction_reference_id": self.extraction_reference_id,
            "document_reference": self.document_reference,
            "original_preserved": self.original_preserved,
        }


@dataclass(frozen=True)
class DocumentIndexEntry:
    """
    Entrada uniforme del índice documental.

    Cada entrada representa una única referencia documental.
    """

    index_id: str
    traceability: DocumentIndexTraceability
    status: IndexEntryStatus
    provider_name: str
    requirement_code: str
    project_id: str
    model_reference: str
    query_keys: dict[str, str]
    reuse_prepared: bool
    query_integration_prepared: bool
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "index_id": self.index_id,
            "traceability": self.traceability.to_dict(),
            "status": self.status.value,
            "provider_name": self.provider_name,
            "requirement_code": self.requirement_code,
            "project_id": self.project_id,
            "model_reference": self.model_reference,
            "query_keys": self.query_keys,
            "reuse_prepared": self.reuse_prepared,
            "query_integration_prepared": self.query_integration_prepared,
            "technical_observations": list(self.technical_observations),
        }


@dataclass(frozen=True)
class IndexingIncident:
    """Incidencia detectada durante la indexación."""

    message: str
    severity: IndexingIncidentSeverity = IndexingIncidentSeverity.INFO

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class DocumentIndexRequest:
    """
    Solicitud de indexación documental.

    El DKI recibe exclusivamente Modelos Documentales Internos del IDMB.
    """

    process_id: UUID
    model_result: InternalModelBuildResult
    validation_reference: str = ""
    project_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentIndexResult:
    """Resultado uniforme de la indexación documental."""

    process_id: UUID
    document_id: str
    index_id: str
    entry: DocumentIndexEntry
    incidents: tuple[IndexingIncident, ...]
    original_preserved: bool
    duplicate_prevented: bool
    entries_count: int
    technical_observations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "index_id": self.index_id,
            "entry": self.entry.to_dict(),
            "incidents": [incident.to_dict() for incident in self.incidents],
            "original_preserved": self.original_preserved,
            "duplicate_prevented": self.duplicate_prevented,
            "entries_count": self.entries_count,
            "technical_observations": list(self.technical_observations),
        }
