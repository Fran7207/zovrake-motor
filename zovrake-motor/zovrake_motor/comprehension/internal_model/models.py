"""Modelo Documental Interno y estructuras del IDMB."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationResult
from zovrake_motor.comprehension.internal_model.enums import ModelBuildIncidentSeverity


@dataclass(frozen=True)
class InternalTraceability:
    """
    Trazabilidad completa: documento original → extracción → canónica → modelo interno.
    """

    process_id: UUID
    document_id: str
    model_id: str
    canonical_reference_id: str
    extraction_reference_id: str
    document_reference: str
    adapter_name: str
    format_type: str
    original_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "canonical_reference_id": self.canonical_reference_id,
            "extraction_reference_id": self.extraction_reference_id,
            "document_reference": self.document_reference,
            "adapter_name": self.adapter_name,
            "format_type": self.format_type,
            "original_preserved": self.original_preserved,
        }


@dataclass(frozen=True)
class InternalDocumentEntity:
    """Entidad Documento del Modelo Interno."""

    entity_id: str
    document_id: str
    model_id: str
    canonical_reference: str
    source_reference: str
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "document_id": self.document_id,
            "model_id": self.model_id,
            "canonical_reference": self.canonical_reference,
            "source_reference": self.source_reference,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class InternalProviderEntity:
    """Entidad Proveedor del Modelo Interno."""

    entity_id: str
    provider_id: str
    name: str
    document_id: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "provider_id": self.provider_id,
            "name": self.name,
            "document_id": self.document_id,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class InternalCommercialInformationEntity:
    """Entidad Información Comercial del Modelo Interno."""

    entity_id: str
    document_id: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    currency: str = ""
    total_amount: str = ""
    payment_terms: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "document_id": self.document_id,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "currency": self.currency,
            "total_amount": self.total_amount,
            "payment_terms": self.payment_terms,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class InternalTechnicalInformationEntity:
    """Entidad Información Técnica del Modelo Interno."""

    entity_id: str
    document_id: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    specifications: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "document_id": self.document_id,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "specifications": list(self.specifications),
            "fields": self.fields,
        }


@dataclass(frozen=True)
class InternalItemEntity:
    """Entidad Ítem del Modelo Interno."""

    entity_id: str
    item_id: str
    document_id: str
    description: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    quantity: str = ""
    unit_price: str = ""
    unit: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "item_id": self.item_id,
            "document_id": self.document_id,
            "description": self.description,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "unit": self.unit,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class InternalCommercialConditionEntity:
    """Entidad Condición Comercial del Modelo Interno."""

    entity_id: str
    condition_id: str
    document_id: str
    content: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    condition_type: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "condition_id": self.condition_id,
            "document_id": self.document_id,
            "content": self.content,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "condition_type": self.condition_type,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class InternalObservationEntity:
    """Entidad Observación del Modelo Interno."""

    entity_id: str
    observation_id: str
    document_id: str
    content: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    observation_type: str = ""
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "observation_id": self.observation_id,
            "document_id": self.document_id,
            "content": self.content,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "observation_type": self.observation_type,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class InternalMetadataEntity:
    """Entidad Metadatos del Modelo Interno."""

    entity_id: str
    document_id: str
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    canonical_metadata: dict[str, Any] = field(default_factory=dict)
    extraction_metadata: dict[str, Any] = field(default_factory=dict)
    model_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "document_id": self.document_id,
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "canonical_metadata": self.canonical_metadata,
            "extraction_metadata": self.extraction_metadata,
            "model_fields": self.model_fields,
        }


@dataclass(frozen=True)
class InternalRequirementContextEntity:
    """Entidad Contexto del Requerimiento del Modelo Interno."""

    entity_id: str
    document_id: str
    requirement_code: str
    process_id: UUID
    canonical_reference: str
    extraction_reference: str
    source_reference: str
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "document_id": self.document_id,
            "requirement_code": self.requirement_code,
            "process_id": str(self.process_id),
            "canonical_reference": self.canonical_reference,
            "extraction_reference": self.extraction_reference,
            "source_reference": self.source_reference,
            "fields": self.fields,
        }


@dataclass(frozen=True)
class InternalOriginalReferencesEntity:
    """Referencias al documento original preservadas en el Modelo Interno."""

    entity_id: str
    document_id: str
    document_reference: str
    adapter_name: str
    format_type: str
    canonical_reference_id: str
    extraction_reference_id: str
    original_preserved: bool
    source_reference: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "document_id": self.document_id,
            "document_reference": self.document_reference,
            "adapter_name": self.adapter_name,
            "format_type": self.format_type,
            "canonical_reference_id": self.canonical_reference_id,
            "extraction_reference_id": self.extraction_reference_id,
            "original_preserved": self.original_preserved,
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True)
class InternalDocumentModel:
    """
    Modelo Documental Interno definitivo e inmutable.

    Única fuente de información para módulos posteriores (PM5).
    """

    model_id: str
    traceability: InternalTraceability
    document: InternalDocumentEntity
    provider: InternalProviderEntity
    commercial_information: InternalCommercialInformationEntity
    technical_information: InternalTechnicalInformationEntity
    items: tuple[InternalItemEntity, ...]
    commercial_conditions: tuple[InternalCommercialConditionEntity, ...]
    observations: tuple[InternalObservationEntity, ...]
    metadata: InternalMetadataEntity
    requirement_context: InternalRequirementContextEntity
    original_references: InternalOriginalReferencesEntity
    schema_version: str = "1.0"
    immutable: bool = True
    classification_ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "traceability": self.traceability.to_dict(),
            "document": self.document.to_dict(),
            "provider": self.provider.to_dict(),
            "commercial_information": self.commercial_information.to_dict(),
            "technical_information": self.technical_information.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "commercial_conditions": [condition.to_dict() for condition in self.commercial_conditions],
            "observations": [observation.to_dict() for observation in self.observations],
            "metadata": self.metadata.to_dict(),
            "requirement_context": self.requirement_context.to_dict(),
            "original_references": self.original_references.to_dict(),
            "schema_version": self.schema_version,
            "immutable": self.immutable,
            "classification_ready": self.classification_ready,
        }


@dataclass(frozen=True)
class ModelBuildIncident:
    """Incidencia detectada durante la construcción del modelo."""

    builder_name: str
    message: str
    severity: ModelBuildIncidentSeverity = ModelBuildIncidentSeverity.INFO

    def to_dict(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class EntityBuildResult:
    """Resultado individual de un constructor de entidad."""

    entity_type: str
    builder_name: str
    incidents: tuple[ModelBuildIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class InternalModelBuildRequest:
    """
    Solicitud de construcción del Modelo Documental Interno.

    El IDMB recibe exclusivamente la Representación Canónica.
    """

    process_id: UUID
    canonical_result: CanonicalRepresentationResult
    requirement_code: str = ""
    requirement_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InternalModelBuildResult:
    """Resultado uniforme de la construcción del Modelo Documental Interno."""

    process_id: UUID
    document_id: str
    model: InternalDocumentModel
    incidents: tuple[ModelBuildIncident, ...]
    original_preserved: bool
    classification_integration_prepared: bool
    builders_executed: int
    technical_observations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model": self.model.to_dict(),
            "incidents": [incident.to_dict() for incident in self.incidents],
            "original_preserved": self.original_preserved,
            "classification_integration_prepared": self.classification_integration_prepared,
            "builders_executed": self.builders_executed,
            "technical_observations": list(self.technical_observations),
        }
