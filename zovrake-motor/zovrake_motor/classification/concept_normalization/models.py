"""Modelos del Concept Normalization Engine y catálogo de conceptos normalizados."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_normalization.enums import (
    ConceptNormalizationStatus,
    ConceptNormalizerType,
    NormalizedConceptCategory,
)


@dataclass(frozen=True)
class NormalizedModelReference:
    """Referencia al registro de origen (material o servicio) y al concepto CAE."""

    model_id: str
    document_id: str
    concept_id: str
    source_record_id: str
    source_category: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "document_id": self.document_id,
            "concept_id": self.concept_id,
            "source_record_id": self.source_record_id,
            "source_category": self.source_category,
        }


@dataclass(frozen=True)
class NormalizedConceptTraceability:
    """Trazabilidad completa del concepto normalizado hacia el origen documental."""

    process_id: UUID
    document_id: str
    model_id: str
    concept_id: str
    source_material_catalog_id: str
    source_service_catalog_id: str
    document_reference: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    adapter_name: str
    format_type: str
    original_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "concept_id": self.concept_id,
            "source_material_catalog_id": self.source_material_catalog_id,
            "source_service_catalog_id": self.source_service_catalog_id,
            "document_reference": self.document_reference,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "adapter_name": self.adapter_name,
            "format_type": self.format_type,
            "original_preserved": self.original_preserved,
        }


@dataclass(frozen=True)
class NormalizedConceptRecord:
    """Registro uniforme de un concepto normalizado."""

    normalized_concept_id: str
    original_value: str
    normalized_value: str
    concept_type: str
    source_category: str
    concept_id: str
    model_reference: NormalizedModelReference
    traceability: NormalizedConceptTraceability
    status: ConceptNormalizationStatus = ConceptNormalizationStatus.NORMALIZED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalized_concept_id": self.normalized_concept_id,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "concept_type": self.concept_type,
            "source_category": self.source_category,
            "concept_id": self.concept_id,
            "model_reference": self.model_reference.to_dict(),
            "traceability": self.traceability.to_dict(),
            "status": self.status.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class NormalizedConceptCatalog:
    """Catálogo uniforme de conceptos normalizados."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_material_catalog_id: str
    source_service_catalog_id: str
    concepts: tuple[NormalizedConceptRecord, ...]
    equivalence_detection_prepared: bool = True
    comparable_group_builder_prepared: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_material_catalog_id": self.source_material_catalog_id,
            "source_service_catalog_id": self.source_service_catalog_id,
            "concepts": [concept.to_dict() for concept in self.concepts],
            "concepts_count": len(self.concepts),
            "equivalence_detection_prepared": self.equivalence_detection_prepared,
            "comparable_group_builder_prepared": self.comparable_group_builder_prepared,
        }


@dataclass(frozen=True)
class ConceptNormalizationIncident:
    """Incidencia detectada durante la normalización conceptual."""

    normalizer_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalizer_name": self.normalizer_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class NormalizerResult:
    """Resultado individual de un normalizador."""

    normalizer_type: ConceptNormalizerType
    normalizer_name: str
    concepts: tuple[NormalizedConceptRecord, ...] = ()
    incidents: tuple[ConceptNormalizationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConceptNormalizationRequest:
    """
    Solicitud de normalización conceptual.

    El CNE consume exclusivamente los catálogos del MCE y SCE.
    """

    process_id: UUID
    material_catalog: dict[str, Any]
    service_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConceptNormalizationResult:
    """Resultado uniforme de la normalización conceptual."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: NormalizedConceptCatalog
    status: ConceptNormalizationStatus
    incidents: tuple[ConceptNormalizationIncident, ...]
    source_catalogs_preserved: bool
    normalizers_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "source_catalogs_preserved": self.source_catalogs_preserved,
            "normalizers_executed": self.normalizers_executed,
            "technical_observations": list(self.technical_observations),
        }
