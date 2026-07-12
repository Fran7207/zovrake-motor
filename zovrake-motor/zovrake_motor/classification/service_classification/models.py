"""Modelos del Service Classification Engine y catálogo de servicios."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.service_classification.enums import (
    ServiceClassificationStatus,
    ServiceClassifierType,
)


@dataclass(frozen=True)
class ServiceModelReference:
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
class ServiceTraceability:
    """Trazabilidad completa del servicio hacia el origen documental."""

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
class ServiceCommercialInformation:
    """Información comercial asociada al servicio."""

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
class ServiceTechnicalInformation:
    """Información técnica asociada al servicio."""

    specifications: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "specifications": list(self.specifications),
            "fields": self.fields,
        }


@dataclass(frozen=True)
class ServiceRecord:
    """Registro uniforme de un servicio identificado."""

    service_id: str
    concept_id: str
    original_name: str
    description: str
    service_scope: str
    unit: str
    quantity: str
    commercial_information: ServiceCommercialInformation
    technical_information: ServiceTechnicalInformation
    model_reference: ServiceModelReference
    traceability: ServiceTraceability
    concept_kind: str
    status: ServiceClassificationStatus = ServiceClassificationStatus.CLASSIFIED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "concept_id": self.concept_id,
            "original_name": self.original_name,
            "description": self.description,
            "service_scope": self.service_scope,
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
class ServiceCatalog:
    """Catálogo uniforme de servicios clasificados — independiente del catálogo de materiales."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_concept_catalog_id: str
    services: tuple[ServiceRecord, ...]
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
            "services": [service.to_dict() for service in self.services],
            "services_count": len(self.services),
            "normalization_prepared": self.normalization_prepared,
            "equivalence_detection_prepared": self.equivalence_detection_prepared,
            "comparable_group_builder_prepared": self.comparable_group_builder_prepared,
        }


@dataclass(frozen=True)
class ServiceClassificationIncident:
    """Incidencia detectada durante la clasificación de servicios."""

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
    """Resultado individual de un clasificador de servicios."""

    classifier_type: ServiceClassifierType
    classifier_name: str
    services: tuple[ServiceRecord, ...] = ()
    incidents: tuple[ServiceClassificationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ServiceClassificationRequest:
    """
    Solicitud de clasificación de servicios.

    El SCE consume exclusivamente el catálogo de conceptos del CAE.
    """

    process_id: UUID
    concept_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceClassificationResult:
    """Resultado uniforme de la clasificación de servicios."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ServiceCatalog
    status: ServiceClassificationStatus
    incidents: tuple[ServiceClassificationIncident, ...]
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
