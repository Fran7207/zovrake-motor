"""Modelos del Comparative Model Builder — Modelo Comparativo Definitivo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_model_builder.enums import (
    ComparativeModelBuildStatus,
)


@dataclass(frozen=True)
class DefinitiveCommercialInformation:
    """Información comercial consolidada — sin modificación de origen."""

    fields: dict[str, Any]
    provider_fields: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": self.fields,
            "provider_fields": list(self.provider_fields),
        }


@dataclass(frozen=True)
class DefinitiveTechnicalInformation:
    """Información técnica consolidada — sin modificación de origen."""

    fields: dict[str, Any]
    specifications: tuple[str, ...]
    provider_fields: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": self.fields,
            "specifications": list(self.specifications),
            "provider_fields": list(self.provider_fields),
        }


@dataclass(frozen=True)
class DefinitiveComparativeModel:
    """
    Modelo Comparativo Definitivo — un modelo por Grupo Comparable.

    Contrato oficial de salida del Prompt Maestro 6.
    """

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    dynamic_columns: tuple[dict[str, Any], ...]
    dynamic_rows: tuple[dict[str, Any], ...]
    provider_organization: tuple[dict[str, Any], ...]
    commercial_information: DefinitiveCommercialInformation
    technical_information: DefinitiveTechnicalInformation
    inherited_context: dict[str, Any]
    confidence_level_available: str
    metadata: dict[str, Any]
    traceability: dict[str, Any]
    motor_internal_references: dict[str, str]
    integrity_status: str
    source_data_preserved: bool = True
    domain_model_preserved: bool = True
    document_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "dynamic_columns": list(self.dynamic_columns),
            "dynamic_columns_count": len(self.dynamic_columns),
            "dynamic_rows": list(self.dynamic_rows),
            "dynamic_rows_count": len(self.dynamic_rows),
            "provider_organization": list(self.provider_organization),
            "providers_count": len(self.provider_organization),
            "commercial_information": self.commercial_information.to_dict(),
            "technical_information": self.technical_information.to_dict(),
            "inherited_context": self.inherited_context,
            "confidence_level_available": self.confidence_level_available,
            "metadata": self.metadata,
            "traceability": self.traceability,
            "motor_internal_references": self.motor_internal_references,
            "integrity_status": self.integrity_status,
            "source_data_preserved": self.source_data_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "document_ids": list(self.document_ids),
        }


@dataclass(frozen=True)
class DefinitiveComparativeModelCatalog:
    """Catálogo de Modelos Comparativos Definitivos del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_enriched_catalog_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    source_provider_catalog_id: str
    source_integrity_report_id: str
    models: tuple[DefinitiveComparativeModel, ...]
    pm6_definitive_output_contract: bool = True
    pm7_input_contract_prepared: bool = True
    comparative_validation_framework_prepared: bool = True
    enriched_catalog_preserved: bool = True
    structure_catalog_preserved: bool = True
    column_catalog_preserved: bool = True
    row_catalog_preserved: bool = True
    provider_catalog_preserved: bool = True
    integrity_report_preserved: bool = True
    domain_model_preserved: bool = True
    source_data_preserved: bool = True
    document_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_enriched_catalog_id": self.source_enriched_catalog_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
            "source_provider_catalog_id": self.source_provider_catalog_id,
            "source_integrity_report_id": self.source_integrity_report_id,
            "models": [model.to_dict() for model in self.models],
            "models_count": len(self.models),
            "pm6_definitive_output_contract": self.pm6_definitive_output_contract,
            "pm7_input_contract_prepared": self.pm7_input_contract_prepared,
            "comparative_validation_framework_prepared": (
                self.comparative_validation_framework_prepared
            ),
            "enriched_catalog_preserved": self.enriched_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "integrity_report_preserved": self.integrity_report_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "document_ids": list(self.document_ids),
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class ModelBuilderResult:
    """Resultado individual de un constructor de modelos."""

    builder_type: str
    builder_name: str
    models: tuple[DefinitiveComparativeModel, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparativeModelBuildRequest:
    """
    Solicitud de construcción del Modelo Comparativo Definitivo.

    El CMB consume exclusivamente catálogos del CSE, DCB, DRB, POE, GIE y TME.
    """

    process_id: UUID
    enriched_catalog: dict[str, Any]
    structure_catalog: dict[str, Any]
    column_catalog: dict[str, Any]
    row_catalog: dict[str, Any]
    provider_catalog: dict[str, Any]
    integrity_report: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeModelBuildResult:
    """Resultado uniforme de la construcción del Modelo Comparativo Definitivo."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: DefinitiveComparativeModelCatalog
    status: ComparativeModelBuildStatus
    models_built_count: int
    enriched_catalog_preserved: bool
    structure_catalog_preserved: bool
    column_catalog_preserved: bool
    row_catalog_preserved: bool
    provider_catalog_preserved: bool
    integrity_report_preserved: bool
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
            "models_built_count": self.models_built_count,
            "enriched_catalog_preserved": self.enriched_catalog_preserved,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "integrity_report_preserved": self.integrity_report_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "builders_executed": self.builders_executed,
            "technical_observations": list(self.technical_observations),
        }