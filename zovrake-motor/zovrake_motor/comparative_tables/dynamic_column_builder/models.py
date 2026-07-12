"""Modelos del Dynamic Column Builder — definición dinámica de columnas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.dynamic_column_builder.enums import (
    ColumnDataType,
    ComparativeColumnBuildStatus,
)


@dataclass(frozen=True)
class ComparativeTableColumnTraceability:
    """Trazabilidad de una columna dinámica."""

    process_id: UUID
    document_id: str
    model_id: str
    source_structure_catalog_id: str
    source_table_id: str
    source_group_id: str
    source_comparative_model_id: str
    attribute_source: str
    structure_catalog_preserved: bool
    domain_model_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_table_id": self.source_table_id,
            "source_group_id": self.source_group_id,
            "source_comparative_model_id": self.source_comparative_model_id,
            "attribute_source": self.attribute_source,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeTableColumnDefinition:
    """
    Modelo interno de columna dinámica.

    Sin valores de proveedores en esta etapa.
    """

    column_id: str
    internal_column_id: str
    attribute_name: str
    data_type: ColumnDataType
    logical_position: int
    group_id: str
    table_id: str
    traceability: ComparativeTableColumnTraceability
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "column_id": self.column_id,
            "internal_column_id": self.internal_column_id,
            "attribute_name": self.attribute_name,
            "data_type": self.data_type.value,
            "logical_position": self.logical_position,
            "group_id": self.group_id,
            "table_id": self.table_id,
            "traceability": self.traceability.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparativeTableColumnSet:
    """Conjunto de columnas dinámicas para un Cuadro Comparativo."""

    table_id: str
    group_id: str
    columns: tuple[ComparativeTableColumnDefinition, ...]
    source_structure_catalog_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "group_id": self.group_id,
            "columns": [column.to_dict() for column in self.columns],
            "columns_count": len(self.columns),
            "source_structure_catalog_id": self.source_structure_catalog_id,
        }


@dataclass(frozen=True)
class ComparativeTableColumnCatalog:
    """Catálogo de columnas dinámicas del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    column_sets: tuple[ComparativeTableColumnSet, ...]
    dynamic_row_builder_prepared: bool = True
    structure_catalog_preserved: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "column_sets": [column_set.to_dict() for column_set in self.column_sets],
            "column_sets_count": len(self.column_sets),
            "dynamic_row_builder_prepared": self.dynamic_row_builder_prepared,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeColumnBuildIncident:
    """Incidencia detectada durante la construcción de columnas."""

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
class ColumnBuilderResult:
    """Resultado individual de un constructor de columnas."""

    builder_type: str
    builder_name: str
    column_sets: tuple[ComparativeTableColumnSet, ...] = ()
    incidents: tuple[ComparativeColumnBuildIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparativeColumnBuildRequest:
    """
    Solicitud de construcción de columnas dinámicas.

    El DCB consume exclusivamente el catálogo de estructuras del CSE.
    """

    process_id: UUID
    structure_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeColumnBuildResult:
    """Resultado uniforme de la construcción de columnas dinámicas."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ComparativeTableColumnCatalog
    status: ComparativeColumnBuildStatus
    incidents: tuple[ComparativeColumnBuildIncident, ...]
    structure_catalog_preserved: bool
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
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "builders_executed": self.builders_executed,
            "technical_observations": list(self.technical_observations),
        }
