"""Modelo Canónico y estructuras del Canonical Representation Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.canonical.enums import TransformationIncidentSeverity
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


@dataclass(frozen=True)
class CanonicalTraceability:
    """
    Trazabilidad entre documento original, extracción y representación canónica.

    Nunca pierde la relación con el documento de origen.
    """

    process_id: UUID
    document_id: str
    adapter_name: str
    document_reference: str
    format_type: str
    extraction_reference_id: str
    original_preserved: bool
    extraction_extractors_executed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "adapter_name": self.adapter_name,
            "document_reference": self.document_reference,
            "format_type": self.format_type,
            "extraction_reference_id": self.extraction_reference_id,
            "original_preserved": self.original_preserved,
            "extraction_extractors_executed": self.extraction_extractors_executed,
        }


@dataclass(frozen=True)
class CanonicalProvider:
    """Proveedor en la Representación Canónica."""

    provider_id: str
    name: str
    source_reference: str
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "source_reference": self.source_reference,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class CanonicalCommercialInformation:
    """Información comercial en la Representación Canónica."""

    source_reference: str
    currency: str = ""
    total_amount: str = ""
    payment_terms: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_reference": self.source_reference,
            "currency": self.currency,
            "total_amount": self.total_amount,
            "payment_terms": self.payment_terms,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class CanonicalTechnicalInformation:
    """Información técnica en la Representación Canónica."""

    source_reference: str
    specifications: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_reference": self.source_reference,
            "specifications": list(self.specifications),
            "fields": self.fields,
        }


@dataclass(frozen=True)
class CanonicalItem:
    """Ítem en la Representación Canónica."""

    item_id: str
    description: str
    source_reference: str
    quantity: str = ""
    unit_price: str = ""
    unit: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "description": self.description,
            "source_reference": self.source_reference,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "unit": self.unit,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class CanonicalCondition:
    """Condición en la Representación Canónica."""

    condition_id: str
    content: str
    source_reference: str
    condition_type: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "content": self.content,
            "source_reference": self.source_reference,
            "condition_type": self.condition_type,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class CanonicalObservation:
    """Observación en la Representación Canónica."""

    observation_id: str
    content: str
    source_reference: str
    observation_type: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "content": self.content,
            "source_reference": self.source_reference,
            "observation_type": self.observation_type,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class CanonicalMetadata:
    """Metadatos en la Representación Canónica."""

    source_reference: str
    extraction_metadata: dict[str, Any] = field(default_factory=dict)
    canonical_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_reference": self.source_reference,
            "extraction_metadata": self.extraction_metadata,
            "canonical_fields": self.canonical_fields,
        }


@dataclass(frozen=True)
class CanonicalDocument:
    """
    Representación Canónica uniforme e inmutable de un documento.

    Toda información se representa mediante este único modelo interno.
    """

    traceability: CanonicalTraceability
    provider: CanonicalProvider
    commercial_information: CanonicalCommercialInformation
    technical_information: CanonicalTechnicalInformation
    items: tuple[CanonicalItem, ...]
    conditions: tuple[CanonicalCondition, ...]
    observations: tuple[CanonicalObservation, ...]
    metadata: CanonicalMetadata
    schema_version: str = "1.0"
    immutable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceability": self.traceability.to_dict(),
            "provider": self.provider.to_dict(),
            "commercial_information": self.commercial_information.to_dict(),
            "technical_information": self.technical_information.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "conditions": [condition.to_dict() for condition in self.conditions],
            "observations": [observation.to_dict() for observation in self.observations],
            "metadata": self.metadata.to_dict(),
            "schema_version": self.schema_version,
            "immutable": self.immutable,
        }


@dataclass(frozen=True)
class TransformationIncident:
    """Incidencia detectada durante la transformación canónica."""

    transformer_name: str
    message: str
    severity: TransformationIncidentSeverity = TransformationIncidentSeverity.INFO

    def to_dict(self) -> dict[str, Any]:
        return {
            "transformer_name": self.transformer_name,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class SectionTransformationResult:
    """Resultado individual de un transformador de sección."""

    section_type: str
    transformer_name: str
    incidents: tuple[TransformationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalRepresentationRequest:
    """
    Solicitud de representación canónica.

    El CRE recibe exclusivamente la salida del Content Extraction Engine.
    """

    process_id: UUID
    extraction_result: ContentExtractionResult


@dataclass(frozen=True)
class CanonicalRepresentationResult:
    """Resultado uniforme de la transformación canónica."""

    process_id: UUID
    document_id: str
    representation: CanonicalDocument
    incidents: tuple[TransformationIncident, ...]
    original_preserved: bool
    classification_integration_prepared: bool
    transformers_executed: int
    technical_observations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "representation": self.representation.to_dict(),
            "incidents": [incident.to_dict() for incident in self.incidents],
            "original_preserved": self.original_preserved,
            "classification_integration_prepared": self.classification_integration_prepared,
            "transformers_executed": self.transformers_executed,
            "technical_observations": list(self.technical_observations),
        }
