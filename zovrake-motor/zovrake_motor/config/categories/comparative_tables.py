"""Configuración del Módulo de Generación de Cuadros Comparativos."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ComparativeQualityFrameworkSettings:
    """
    Configuración del Comparative Quality Framework — fuente centralizada.

    Sin activar certificación final del módulo en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    architectural_compliance_validator_enabled: bool = True
    definitive_model_consistency_validator_enabled: bool = True
    validation_report_integrity_validator_enabled: bool = True
    identifier_uniqueness_validator_enabled: bool = True
    traceability_chain_validator_enabled: bool = True
    pipeline_flow_validator_enabled: bool = True
    require_pipeline_snapshot: bool = False
    allow_empty_catalog_validation: bool = True
    fail_on_error_findings: bool = True
    max_tables_per_process: int = 5_000
    max_groups_per_process: int = 5_000
    max_providers_per_process: int = 500
    module_certification_prepared: bool = True

    @classmethod
    def default(cls) -> ComparativeQualityFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class ComparativeValidationFrameworkSettings:
    """
    Configuración del Comparative Validation Framework — fuente centralizada.

    Sin modificar ni corregir datos en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_findings_per_report: int = 50_000
    definitive_comparative_model_validator_enabled: bool = True
    finding_id_prefix: str = "CVF"
    finding_id_padding: int = 6
    max_errors_before_invalid: int = 1
    comparative_quality_framework_prepared: bool = True

    @classmethod
    def default(cls) -> ComparativeValidationFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class ComparativeModelBuilderSettings:
    """
    Configuración del Comparative Model Builder — fuente centralizada.

    Sin generar representación visual ni resultados de análisis en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_models_per_process: int = 5_000
    group_comparative_model_builder_enabled: bool = True
    definitive_model_id_prefix: str = "CMD"
    definitive_model_id_padding: int = 6
    comparative_validation_framework_prepared: bool = True

    @classmethod
    def default(cls) -> ComparativeModelBuilderSettings:
        return cls()


@dataclass(frozen=True)
class TraceabilityMetadataEngineSettings:
    """
    Configuración del Traceability & Metadata Engine — fuente centralizada.

    Sin modificar datos de origen en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_enriched_tables_per_process: int = 5_000
    comparative_table_metadata_enricher_enabled: bool = True
    enrichment_id_prefix: str = "TME"
    enrichment_id_padding: int = 6
    comparative_model_builder_prepared: bool = True

    @classmethod
    def default(cls) -> TraceabilityMetadataEngineSettings:
        return cls()


@dataclass(frozen=True)
class GroupIntegrityEngineSettings:
    """
    Configuración del Group Integrity Engine — fuente centralizada.

    Sin modificar ni corregir datos en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_findings_per_report: int = 50_000
    comparative_table_integrity_validator_enabled: bool = True
    finding_id_prefix: str = "GIC"
    finding_id_padding: int = 6
    max_errors_before_invalid: int = 1
    traceability_metadata_engine_prepared: bool = True

    @classmethod
    def default(cls) -> GroupIntegrityEngineSettings:
        return cls()


@dataclass(frozen=True)
class ProviderOrganizationEngineSettings:
    """
    Configuración del Provider Organization Engine — fuente centralizada.

    Sin comparar, recomendar ni aplicar reglas de negocio en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_providers_per_organization: int = 500
    group_provider_organizer_enabled: bool = True
    organization_id_prefix: str = "DOP"
    organization_id_padding: int = 6
    organization_id_immutable: bool = True
    deterministic_sort_enabled: bool = True
    group_integrity_engine_prepared: bool = True

    @classmethod
    def default(cls) -> ProviderOrganizationEngineSettings:
        return cls()


@dataclass(frozen=True)
class DynamicRowBuilderSettings:
    """
    Configuración del Dynamic Row Builder — fuente centralizada.

    Sin poblar celdas ni organizar proveedores en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_rows_per_process: int = 50_000
    provider_row_builder_enabled: bool = True
    row_id_prefix: str = "DCR"
    row_id_padding: int = 6
    row_id_immutable: bool = True
    provider_organization_engine_prepared: bool = True

    @classmethod
    def default(cls) -> DynamicRowBuilderSettings:
        return cls()


@dataclass(frozen=True)
class DynamicColumnBuilderSettings:
    """
    Configuración del Dynamic Column Builder — fuente centralizada.

    Sin activar filas dinámicas ni valores de proveedor en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_columns_per_process: int = 50_000
    structure_attribute_column_builder_enabled: bool = True
    column_id_prefix: str = "DCC"
    column_id_padding: int = 6
    column_id_immutable: bool = True
    dynamic_row_builder_prepared: bool = True

    @classmethod
    def default(cls) -> DynamicColumnBuilderSettings:
        return cls()


@dataclass(frozen=True)
class ComparativeStructureEngineSettings:
    """
    Configuración del Comparative Structure Engine — fuente centralizada.

    Sin activar columnas ni filas dinámicas en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_structures_per_process: int = 5_000
    domain_model_group_structure_builder_enabled: bool = True
    structure_id_prefix: str = "CTS"
    structure_id_padding: int = 6
    structure_id_immutable: bool = True
    dynamic_column_builder_prepared: bool = True
    dynamic_row_builder_prepared: bool = True

    @classmethod
    def default(cls) -> ComparativeStructureEngineSettings:
        return cls()


@dataclass(frozen=True)
class ComparativeTablesSettings:
    """
    Configuración de Generación de Cuadros Comparativos — fuente centralizada.

    Sin activar generación completa de cuadros comparativos en esta etapa.
    """

    enabled: bool = False
    max_tables_per_process: int = 5_000
    max_groups_per_process: int = 5_000
    max_providers_per_process: int = 500
    classification_integration_prepared: bool = True
    classification_enabled: bool = False
    pm6_output_contract_required: bool = True
    comparative_structure_engine: ComparativeStructureEngineSettings = field(
        default_factory=ComparativeStructureEngineSettings.default,
    )
    dynamic_column_builder: DynamicColumnBuilderSettings = field(
        default_factory=DynamicColumnBuilderSettings.default,
    )
    dynamic_row_builder: DynamicRowBuilderSettings = field(
        default_factory=DynamicRowBuilderSettings.default,
    )
    provider_organization_engine: ProviderOrganizationEngineSettings = field(
        default_factory=ProviderOrganizationEngineSettings.default,
    )
    group_integrity_engine: GroupIntegrityEngineSettings = field(
        default_factory=GroupIntegrityEngineSettings.default,
    )
    traceability_metadata_engine: TraceabilityMetadataEngineSettings = field(
        default_factory=TraceabilityMetadataEngineSettings.default,
    )
    comparative_model_builder: ComparativeModelBuilderSettings = field(
        default_factory=ComparativeModelBuilderSettings.default,
    )
    comparative_validation_framework: ComparativeValidationFrameworkSettings = field(
        default_factory=ComparativeValidationFrameworkSettings.default,
    )
    comparative_quality_framework: ComparativeQualityFrameworkSettings = field(
        default_factory=ComparativeQualityFrameworkSettings.default,
    )

    @classmethod
    def default(cls) -> ComparativeTablesSettings:
        return cls()
