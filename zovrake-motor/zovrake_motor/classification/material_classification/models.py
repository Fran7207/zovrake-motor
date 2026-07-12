"""Modelos del Material Classification Engine y catálogo de materiales."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.material_classification.enums import (
    MaterialClassificationStatus,
    MaterialClassifierType,
)


@dataclass(frozen=True)
class MaterialModelReference:
    """Referencia al Modelo Documental Interno y al concepto CAE."""

    model_id: str
    document_id: str
    concept_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "document_id": self.document_id,
            "concept_id": self.concept_id,
        }


@dataclass(frozen=True)
class MaterialTraceability:
    """Trazabilidad completa del material hacia el origen documental."""

    process_id: UUID
    document_id: str
    model_id: str
    concept_id: str
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
            "document_reference": self.document_reference,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "adapter_name": self.adapter_name,
            "format_type": self.format_type,
            "original_preserved": self.original_preserved,
        }


@dataclass(frozen=True)
class MaterialCommercialInformation:
    """Información comercial asociada al material."""

    unit_price: str = ""
    currency: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_price": self.unit_price,
            "currency": self.currency,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class MaterialTechnicalInformation:
    """Información técnica asociada al material."""

    specifications: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "specifications": list(self.specifications),
            "fields": self.fields,
        }


@dataclass(frozen=True)
class MaterialRecord:
    """Registro uniforme de un material identificado."""

    material_id: str
    concept_id: str
    original_name: str
    description: str
    unit: str
    quantity: str
    commercial_information: MaterialCommercialInformation
    technical_information: MaterialTechnicalInformation
    model_reference: MaterialModelReference
    traceability: MaterialTraceability
    concept_kind: str
    status: MaterialClassificationStatus = MaterialClassificationStatus.CLASSIFIED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_id": self.material_id,
            "concept_id": self.concept_id,
            "original_name": self.original_name,
            "description": self.description,
            "unit": self.unit,
            "quantity": self.quantity,
            "commercial_information": self.commercial_information.to_dict(),
            "technical_information": self.technical_information.to_dict(),
            "model_reference": self.model_reference.to_dict(),
            "traceability": self.traceability.to_dict(),
            "concept_kind": self.concept_kind,
            "status": self.status.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MaterialCatalog:
    """Catálogo uniforme de materiales clasificados."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_concept_catalog_id: str
    materials: tuple[MaterialRecord, ...]
    service_classification_prepared: bool = True
    normalization_prepared: bool = True
    equivalence_detection_prepared: bool = True
    comparable_group_builder_prepared: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_concept_catalog_id": self.source_concept_catalog_id,
            "materials": [material.to_dict() for material in self.materials],
            "materials_count": len(self.materials),
            "service_classification_prepared": self.service_classification_prepared,
            "normalization_prepared": self.normalization_prepared,
            "equivalence_detection_prepared": self.equivalence_detection_prepared,
            "comparable_group_builder_prepared": self.comparable_group_builder_prepared,
        }


@dataclass(frozen=True)
class MaterialClassificationIncident:
    """Incidencia detectada durante la clasificación de materiales."""

    classifier_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "classifier_name": self.classifier_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ClassifierResult:
    """Resultado individual de un clasificador de materiales."""

    classifier_type: MaterialClassifierType
    classifier_name: str
    materials: tuple[MaterialRecord, ...] = ()
    incidents: tuple[MaterialClassificationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class MaterialClassificationRequest:
    """
    Solicitud de clasificación de materiales.

    El MCE consume exclusivamente el catálogo de conceptos del CAE.
    """

    process_id: UUID
    concept_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MaterialClassificationResult:
    """Resultado uniforme de la clasificación de materiales."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: MaterialCatalog
    status: MaterialClassificationStatus
    incidents: tuple[MaterialClassificationIncident, ...]
    concept_catalog_preserved: bool
    classifiers_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "concept_catalog_preserved": self.concept_catalog_preserved,
            "classifiers_executed": self.classifiers_executed,
            "technical_observations": list(self.technical_observations),
        }
