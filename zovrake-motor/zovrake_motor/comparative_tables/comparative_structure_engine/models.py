"""Modelos del Comparative Structure Engine — estructura base del cuadro comparativo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_structure_engine.enums import (
    ComparativeTableStructureStatus,
)


@dataclass(frozen=True)
class ComparativeTableDomainReference:
    """Referencias al Modelo Comparativo de Dominio — sin modificación."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    comparative_model_id: str
    pm6_output_contract: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "comparative_model_id": self.comparative_model_id,
            "pm6_output_contract": self.pm6_output_contract,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class ComparativeTableStructureTraceability:
    """Trazabilidad completa de la estructura base — cadena preservada desde PM5."""

    process_id: UUID
    document_id: str
    model_id: str
    source_domain_catalog_id: str
    source_comparative_model_id: str
    group_id: str
    lineage: dict[str, Any]
    source_data_preserved: bool
    domain_model_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "source_domain_catalog_id": self.source_domain_catalog_id,
            "source_comparative_model_id": self.source_comparative_model_id,
            "group_id": self.group_id,
            "lineage": self.lineage,
            "source_data_preserved": self.source_data_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeTableBaseStructure:
    """
    Modelo Base del Cuadro Comparativo — una estructura por Grupo Comparable.

    Espacios preparados para columnas, filas, proveedores, metadatos y validaciones.
    """

    table_id: str
    internal_table_id: str
    group_id: str
    group_type: str
    table_status: ComparativeTableStructureStatus
    domain_reference: ComparativeTableDomainReference
    columns_prepared: tuple[str, ...] = ()
    rows_prepared: tuple[str, ...] = ()
    providers_prepared: tuple[str, ...] = ()
    metadata_prepared: dict[str, Any] = field(default_factory=dict)
    validation_prepared: dict[str, Any] = field(default_factory=dict)
    traceability: ComparativeTableStructureTraceability | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "internal_table_id": self.internal_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "table_status": self.table_status.value,
            "domain_reference": self.domain_reference.to_dict(),
            "columns_prepared": list(self.columns_prepared),
            "rows_prepared": list(self.rows_prepared),
            "providers_prepared": list(self.providers_prepared),
            "metadata_prepared": self.metadata_prepared,
            "validation_prepared": self.validation_prepared,
            "traceability": self.traceability.to_dict() if self.traceability is not None else None,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparativeTableStructureCatalog:
    """Catálogo de estructuras base de cuadros comparativos."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_domain_catalog_id: str
    structures: tuple[ComparativeTableBaseStructure, ...]
    dynamic_column_builder_prepared: bool = True
    dynamic_row_builder_prepared: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_domain_catalog_id": self.source_domain_catalog_id,
            "structures": [structure.to_dict() for structure in self.structures],
            "structures_count": len(self.structures),
            "dynamic_column_builder_prepared": self.dynamic_column_builder_prepared,
            "dynamic_row_builder_prepared": self.dynamic_row_builder_prepared,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeStructureBuildIncident:
    """Incidencia detectada durante la construcción de estructuras."""

    builder_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class StructureBuilderResult:
    """Resultado individual de un constructor de estructuras."""

    builder_type: str
    builder_name: str
    structures: tuple[ComparativeTableBaseStructure, ...] = ()
    incidents: tuple[ComparativeStructureBuildIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparativeStructureBuildRequest:
    """
    Solicitud de construcción de estructuras comparativas.

    El CSE consume exclusivamente el catálogo del Modelo Comparativo de Dominio.
    """

    process_id: UUID
    domain_model_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeStructureBuildResult:
    """Resultado uniforme de la construcción de estructuras comparativas."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ComparativeTableStructureCatalog
    status: ComparativeTableStructureStatus
    incidents: tuple[ComparativeStructureBuildIncident, ...]
    domain_model_preserved: bool
    builders_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "domain_model_preserved": self.domain_model_preserved,
            "builders_executed": self.builders_executed,
            "technical_observations": list(self.technical_observations),
        }
