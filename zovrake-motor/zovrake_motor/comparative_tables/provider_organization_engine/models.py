"""Modelos del Provider Organization Engine — organización de proveedores."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.provider_organization_engine.enums import (
    ProviderOrganizationBuildStatus,
)


@dataclass(frozen=True)
class OrganizedProviderTraceability:
    """Trazabilidad completa de un proveedor organizado."""

    process_id: UUID
    document_id: str
    model_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    source_table_id: str
    source_group_id: str
    source_row_id: str
    source_provider_id: str
    source_document_reference: str
    column_catalog_preserved: bool
    structure_catalog_preserved: bool
    row_catalog_preserved: bool
    domain_model_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
            "source_table_id": self.source_table_id,
            "source_group_id": self.source_group_id,
            "source_row_id": self.source_row_id,
            "source_provider_id": self.source_provider_id,
            "source_document_reference": self.source_document_reference,
            "column_catalog_preserved": self.column_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class OrganizedProviderCommercialInformation:
    """Información comercial heredada — sin modificación."""

    fields: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"fields": self.fields}


@dataclass(frozen=True)
class OrganizedProviderTechnicalInformation:
    """Información técnica heredada — sin modificación."""

    fields: dict[str, Any]
    specifications: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": self.fields,
            "specifications": list(self.specifications),
        }


@dataclass(frozen=True)
class OrganizedProviderRecord:
    """
    Modelo interno del proveedor organizado.

    Conserva identidad y referencias sin alterar la información original.
    """

    organization_id: str
    internal_organization_id: str
    provider_id: str
    group_id: str
    table_id: str
    row_id: str
    row_reference: str
    document_reference: str
    commercial_information: OrganizedProviderCommercialInformation
    technical_information: OrganizedProviderTechnicalInformation
    inherited_context: dict[str, Any]
    confidence_level_available: str
    logical_position: int
    column_references: tuple[str, ...]
    traceability: OrganizedProviderTraceability
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "internal_organization_id": self.internal_organization_id,
            "provider_id": self.provider_id,
            "group_id": self.group_id,
            "table_id": self.table_id,
            "row_id": self.row_id,
            "row_reference": self.row_reference,
            "document_reference": self.document_reference,
            "commercial_information": self.commercial_information.to_dict(),
            "technical_information": self.technical_information.to_dict(),
            "inherited_context": self.inherited_context,
            "confidence_level_available": self.confidence_level_available,
            "logical_position": self.logical_position,
            "column_references": list(self.column_references),
            "traceability": self.traceability.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class OrganizedProviderSet:
    """Conjunto de proveedores organizados para un Grupo Comparable."""

    table_id: str
    group_id: str
    providers: tuple[OrganizedProviderRecord, ...]
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "group_id": self.group_id,
            "providers": [provider.to_dict() for provider in self.providers],
            "providers_count": len(self.providers),
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
        }


@dataclass(frozen=True)
class OrganizedProviderCatalog:
    """Catálogo de proveedores organizados del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    provider_sets: tuple[OrganizedProviderSet, ...]
    group_integrity_engine_prepared: bool = True
    column_catalog_preserved: bool = True
    structure_catalog_preserved: bool = True
    row_catalog_preserved: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
            "provider_sets": [provider_set.to_dict() for provider_set in self.provider_sets],
            "provider_sets_count": len(self.provider_sets),
            "group_integrity_engine_prepared": self.group_integrity_engine_prepared,
            "column_catalog_preserved": self.column_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ProviderOrganizationIncident:
    """Incidencia detectada durante la organización de proveedores."""

    organizer_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "organizer_name": self.organizer_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ProviderOrganizerResult:
    """Resultado individual de un organizador de proveedores."""

    organizer_type: str
    organizer_name: str
    provider_sets: tuple[OrganizedProviderSet, ...] = ()
    incidents: tuple[ProviderOrganizationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderOrganizationBuildRequest:
    """
    Solicitud de organización de proveedores.

    El POE consume exclusivamente los catálogos del CSE, DCB y DRB.
    """

    process_id: UUID
    structure_catalog: dict[str, Any]
    column_catalog: dict[str, Any]
    row_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderOrganizationBuildResult:
    """Resultado uniforme de la organización de proveedores."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: OrganizedProviderCatalog
    status: ProviderOrganizationBuildStatus
    incidents: tuple[ProviderOrganizationIncident, ...]
    column_catalog_preserved: bool
    structure_catalog_preserved: bool
    row_catalog_preserved: bool
    domain_model_preserved: bool
    organizers_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "column_catalog_preserved": self.column_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "organizers_executed": self.organizers_executed,
            "technical_observations": list(self.technical_observations),
        }
