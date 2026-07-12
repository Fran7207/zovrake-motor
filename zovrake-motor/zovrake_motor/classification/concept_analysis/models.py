"""Modelos del Concept Analysis Engine y catálogo temporal de conceptos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_analysis.enums import (
    ConceptAnalysisStatus,
    ConceptDetectorType,
    ConceptKind,
)


@dataclass(frozen=True)
class ConceptLocation:
    """Ubicación del concepto dentro del Modelo Documental Interno."""

    section: str
    entity_id: str
    source_reference: str
    canonical_reference: str
    extraction_reference: str
    entity_index: int | None = None
    field_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "entity_id": self.entity_id,
            "entity_index": self.entity_index,
            "field_name": self.field_name,
            "source_reference": self.source_reference,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
        }


@dataclass(frozen=True)
class ConceptTraceability:
    """Trazabilidad completa del concepto hacia el documento original."""

    process_id: UUID
    document_id: str
    model_id: str
    document_reference: str
    adapter_name: str
    format_type: str
    original_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "document_reference": self.document_reference,
            "adapter_name": self.adapter_name,
            "format_type": self.format_type,
            "original_preserved": self.original_preserved,
        }


@dataclass(frozen=True)
class ConceptCandidate:
    """
    Concepto candidato identificado — estructura uniforme del catálogo temporal.

    Sin clasificación material/servicio en esta etapa.
    """

    concept_id: str
    kind: ConceptKind
    original_description: str
    location: ConceptLocation
    traceability: ConceptTraceability
    status: ConceptAnalysisStatus = ConceptAnalysisStatus.IDENTIFIED
    classification_pending: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "kind": self.kind.value,
            "original_description": self.original_description,
            "location": self.location.to_dict(),
            "traceability": self.traceability.to_dict(),
            "status": self.status.value,
            "classification_pending": self.classification_pending,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ConceptCatalog:
    """Catálogo temporal uniforme de conceptos detectados."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    concepts: tuple[ConceptCandidate, ...]
    material_classification_prepared: bool = True
    service_classification_prepared: bool = True
    normalization_prepared: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "concepts": [concept.to_dict() for concept in self.concepts],
            "concepts_count": len(self.concepts),
            "material_classification_prepared": self.material_classification_prepared,
            "service_classification_prepared": self.service_classification_prepared,
            "normalization_prepared": self.normalization_prepared,
        }


@dataclass(frozen=True)
class ConceptAnalysisIncident:
    """Incidencia detectada durante el análisis de conceptos."""

    detector_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector_name": self.detector_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class DetectorResult:
    """Resultado individual de un detector de conceptos."""

    detector_type: ConceptDetectorType
    detector_name: str
    concepts: tuple[ConceptCandidate, ...] = ()
    incidents: tuple[ConceptAnalysisIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConceptAnalysisRequest:
    """
    Solicitud de análisis de conceptos.

    El CAE consume exclusivamente el Modelo Documental Interno serializado.
    """

    process_id: UUID
    internal_model: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConceptAnalysisResult:
    """Resultado uniforme del análisis de conceptos."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ConceptCatalog
    status: ConceptAnalysisStatus
    incidents: tuple[ConceptAnalysisIncident, ...]
    internal_model_preserved: bool
    detectors_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "internal_model_preserved": self.internal_model_preserved,
            "detectors_executed": self.detectors_executed,
            "technical_observations": list(self.technical_observations),
        }
