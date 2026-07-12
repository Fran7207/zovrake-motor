"""Modelos del Dynamic Row Builder — definición dinámica de filas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.dynamic_row_builder.enums import ComparativeRowBuildStatus


@dataclass(frozen=True)
class ComparativeTableCellPlaceholder:
    """Espacio reservado para una celda futura — sin valor en esta etapa."""

    column_id: str
    attribute_name: str
    logical_position: int
    value_prepared: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "column_id": self.column_id,
            "attribute_name": self.attribute_name,
            "logical_position": self.logical_position,
            "value_prepared": self.value_prepared,
        }


@dataclass(frozen=True)
class ComparativeTableRowTraceability:
    """Trazabilidad de una fila dinámica."""

    process_id: UUID
    document_id: str
    model_id: str
    source_column_catalog_id: str
    source_structure_catalog_id: str
    source_table_id: str
    source_group_id: str
    source_provider_id: str
    column_catalog_preserved: bool
    structure_catalog_preserved: bool
    domain_model_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_table_id": self.source_table_id,
            "source_group_id": self.source_group_id,
            "source_provider_id": self.source_provider_id,
            "column_catalog_preserved": self.column_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeTableRowDefinition:
    """
    Modelo interno de fila dinámica.

    Sin valores de celdas en esta etapa.
    """

    row_id: str
    internal_row_id: str
    provider_id: str
    logical_position: int
    group_id: str
    table_id: str
    column_references: tuple[str, ...]
    cells_reserved: tuple[ComparativeTableCellPlaceholder, ...]
    traceability: ComparativeTableRowTraceability
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "internal_row_id": self.internal_row_id,
            "provider_id": self.provider_id,
            "logical_position": self.logical_position,
            "group_id": self.group_id,
            "table_id": self.table_id,
            "column_references": list(self.column_references),
            "cells_reserved": [cell.to_dict() for cell in self.cells_reserved],
            "traceability": self.traceability.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparativeTableRowSet:
    """Conjunto de filas dinámicas para un Cuadro Comparativo."""

    table_id: str
    group_id: str
    rows: tuple[ComparativeTableRowDefinition, ...]
    source_column_catalog_id: str
    source_structure_catalog_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "group_id": self.group_id,
            "rows": [row.to_dict() for row in self.rows],
            "rows_count": len(self.rows),
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
        }


@dataclass(frozen=True)
class ComparativeTableRowCatalog:
    """Catálogo de filas dinámicas del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_column_catalog_id: str
    source_structure_catalog_id: str
    row_sets: tuple[ComparativeTableRowSet, ...]
    provider_organization_engine_prepared: bool = True
    column_catalog_preserved: bool = True
    structure_catalog_preserved: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "row_sets": [row_set.to_dict() for row_set in self.row_sets],
            "row_sets_count": len(self.row_sets),
            "provider_organization_engine_prepared": self.provider_organization_engine_prepared,
            "column_catalog_preserved": self.column_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeRowBuildIncident:
    """Incidencia detectada durante la construcción de filas."""

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
class RowBuilderResult:
    """Resultado individual de un constructor de filas."""

    builder_type: str
    builder_name: str
    row_sets: tuple[ComparativeTableRowSet, ...] = ()
    incidents: tuple[ComparativeRowBuildIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparativeRowBuildRequest:
    """
    Solicitud de construcción de filas dinámicas.

    El DRB consume exclusivamente los catálogos del CSE y el DCB.
    """

    process_id: UUID
    column_catalog: dict[str, Any]
    structure_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeRowBuildResult:
    """Resultado uniforme de la construcción de filas dinámicas."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ComparativeTableRowCatalog
    status: ComparativeRowBuildStatus
    incidents: tuple[ComparativeRowBuildIncident, ...]
    column_catalog_preserved: bool
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
            "column_catalog_preserved": self.column_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "builders_executed": self.builders_executed,
            "technical_observations": list(self.technical_observations),
        }
