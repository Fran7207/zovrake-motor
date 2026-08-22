"""Modelos del Equivalence Detection Engine y catálogo de equivalencias."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.equivalence_detection.enums import (
    EquivalenceDetectionStatus,
    EquivalenceRelationType,
    EvidenceLevel,
    EquivalenceDetectorType,
)


@dataclass(frozen=True)
class EquivalenceExplainability:
    """Información explicativa de una relación detectada."""

    criteria_used: tuple[str, ...]
    information_used: tuple[str, ...]
    limitations: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "criteria_used": list(self.criteria_used),
            "information_used": list(self.information_used),
            "limitations": list(self.limitations),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class EquivalenceTraceability:
    """Trazabilidad completa de una equivalencia hacia el origen documental."""

    process_id: UUID
    document_id: str
    model_id: str
    source_normalized_catalog_id: str
    concept_ids: tuple[str, ...]
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
            "source_normalized_catalog_id": self.source_normalized_catalog_id,
            "concept_ids": list(self.concept_ids),
            "document_reference": self.document_reference,
            "canonical_reference": self.canonical_reference,
            "original_preserved": self.original_preserved,
        }


@dataclass(frozen=True)
class EquivalenceRecord:
    """Registro uniforme de una relación de equivalencia o diferenciación."""

    equivalence_id: str
    involved_concept_ids: tuple[str, ...]
    relation_type: str
    evidence_level: str
    status: str
    detector_type: str
    explainability: EquivalenceExplainability
    traceability: EquivalenceTraceability
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "equivalence_id": self.equivalence_id,
            "involved_concept_ids": list(self.involved_concept_ids),
            "relation_type": self.relation_type,
            "evidence_level": self.evidence_level,
            "status": self.status,
            "detector_type": self.detector_type,
            "explainability": self.explainability.to_dict(),
            "traceability": self.traceability.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EquivalenceCatalog:
    """Catálogo uniforme de relaciones de equivalencia detectadas."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_normalized_catalog_id: str
    equivalences: tuple[EquivalenceRecord, ...]
    document_ids: tuple[str, ...] = ()
    comparable_group_builder_prepared: bool = True
    context_association_prepared: bool = True
    comparative_domain_model_prepared: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "document_ids": list(self.document_ids),
            "source_normalized_catalog_id": self.source_normalized_catalog_id,
            "equivalences": [
                equivalence.to_dict()
                for equivalence in self.equivalences
            ],
            "equivalences_count": len(self.equivalences),
            "comparable_group_builder_prepared": (
                self.comparable_group_builder_prepared
            ),
            "context_association_prepared": (
                self.context_association_prepared
            ),
            "comparative_domain_model_prepared": (
                self.comparative_domain_model_prepared
            ),
        }


@dataclass(frozen=True)
class EquivalenceDetectionIncident:
    """Incidencia detectada durante la detección de equivalencias."""

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
    """Resultado individual de un detector de equivalencias."""

    detector_type: EquivalenceDetectorType
    detector_name: str
    equivalences: tuple[EquivalenceRecord, ...] = ()
    incidents: tuple[EquivalenceDetectionIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class EquivalenceDetectionRequest:
    """
    Solicitud de detección de equivalencias.

    El EDE consume exclusivamente el catálogo del CNE.
    """

    process_id: UUID
    normalized_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EquivalenceDetectionResult:
    """Resultado uniforme de la detección de equivalencias."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: EquivalenceCatalog
    status: EquivalenceDetectionStatus
    incidents: tuple[EquivalenceDetectionIncident, ...]
    normalized_catalog_preserved: bool
    detectors_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [
                incident.to_dict()
                for incident in self.incidents
            ],
            "normalized_catalog_preserved": (
                self.normalized_catalog_preserved
            ),
            "detectors_executed": self.detectors_executed,
            "technical_observations": list(self.technical_observations),
        }