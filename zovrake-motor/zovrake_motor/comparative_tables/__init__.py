"""Módulo de Generación de Cuadros Comparativos — Implementación 4.10 (Prompt Maestro 6)."""

from zovrake_motor.comparative_tables.comparative_structure_engine import (
    ComparativeStructureBuildRequest,
    ComparativeStructureBuildResult,
    ComparativeStructureBuilderEngine,
    ComparativeTableBaseStructure,
    ComparativeTableStructureCatalog,
    DomainModelCatalogAccessError,
)
from zovrake_motor.comparative_tables.dynamic_column_builder import (
    ComparativeColumnBuildRequest,
    ComparativeColumnBuildResult,
    DynamicColumnBuilderEngine,
    ComparativeTableColumnCatalog,
    ComparativeTableColumnDefinition,
    StructureCatalogAccessError,
)
from zovrake_motor.comparative_tables.dynamic_row_builder import (
    ComparativeRowBuildRequest,
    ComparativeRowBuildResult,
    DynamicRowBuilderEngine,
    ComparativeTableRowCatalog,
    ComparativeTableRowDefinition,
    ColumnCatalogAccessError,
)
from zovrake_motor.comparative_tables.provider_organization_engine import (
    OrganizedProviderCatalog,
    OrganizedProviderRecord,
    ProviderOrganizationBuildRequest,
    ProviderOrganizationBuildResult,
    ProviderOrganizationEngineCore,
)
from zovrake_motor.comparative_tables.group_integrity_engine import (
    GroupIntegrityEngineCore,
    GroupIntegrityReport,
    GroupIntegrityValidationRequest,
    GroupIntegrityValidationResult,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine import (
    EnrichedComparativeTableCatalog,
    TraceabilityMetadataEngineCore,
    TraceabilityMetadataEnrichmentRequest,
    TraceabilityMetadataEnrichmentResult,
)
from zovrake_motor.comparative_tables.comparative_model_builder import (
    ComparativeModelBuildRequest,
    ComparativeModelBuildResult,
    ComparativeModelBuilderEngine,
    DefinitiveComparativeModel,
    DefinitiveComparativeModelCatalog,
    PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.comparative_tables.comparative_validation_framework import (
    ComparativeModelValidationRequest,
    ComparativeModelValidationResult,
    ComparativeValidationFrameworkCore,
    ComparativeValidationReport,
)
from zovrake_motor.comparative_tables.comparative_quality_framework import (
    ComparativeQualityFrameworkCore,
    ComparativeQualityValidationRequest,
    ComparativeQualityValidationResult,
    ComparativeQualityReport,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesComponentType, ComparativeTablesPhase
from zovrake_motor.comparative_tables.input_gateway import ClassificationOutputGateway
from zovrake_motor.comparative_tables.input_models import (
    ComparativeDomainModelReference,
    ComparativeTablesInputBundle,
)
from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
from zovrake_motor.comparative_tables.models import (
    ComparativeTablesRequest,
    ComparativeTablesResult,
    ComponentDescriptor,
)
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.comparative_tables.port import ComparativeTablesPort
from zovrake_motor.comparative_tables.registry import ComponentRegistry
from zovrake_motor.comparative_tables.service import ComparativeTablesService

__all__ = [
    "ClassificationOutputGateway",
    "ComparativeColumnBuildRequest",
    "ComparativeColumnBuildResult",
    "ComparativeDomainModelReference",
    "ComparativeStructureBuildRequest",
    "ComparativeStructureBuildResult",
    "ComparativeStructureBuilderEngine",
    "ComparativeTableBaseStructure",
    "ComparativeTableColumnCatalog",
    "ComparativeTableColumnDefinition",
    "ComparativeRowBuildRequest",
    "ComparativeRowBuildResult",
    "ComparativeTableRowCatalog",
    "ComparativeTableRowDefinition",
    "ComparativeTableStructureCatalog",
    "ComparativeTablesComponentType",
    "ComparativeTablesInputBundle",
    "ComparativeTablesMotorIntegration",
    "ComparativeTablesPhase",
    "ComparativeTablesPipeline",
    "ComparativeTablesPort",
    "ComparativeTablesRequest",
    "ComparativeTablesResult",
    "ComparativeTablesService",
    "ComponentDescriptor",
    "ComponentRegistry",
    "DomainModelCatalogAccessError",
    "OrganizedProviderCatalog",
    "OrganizedProviderRecord",
    "ProviderOrganizationBuildRequest",
    "ProviderOrganizationBuildResult",
    "ProviderOrganizationEngineCore",
    "GroupIntegrityEngineCore",
    "GroupIntegrityReport",
    "GroupIntegrityValidationRequest",
    "GroupIntegrityValidationResult",
    "EnrichedComparativeTableCatalog",
    "TraceabilityMetadataEngineCore",
    "TraceabilityMetadataEnrichmentRequest",
    "TraceabilityMetadataEnrichmentResult",
    "ComparativeModelBuildRequest",
    "ComparativeModelBuildResult",
    "ComparativeModelBuilderEngine",
    "DefinitiveComparativeModel",
    "DefinitiveComparativeModelCatalog",
    "PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME",
    "ComparativeModelValidationRequest",
    "ComparativeModelValidationResult",
    "ComparativeValidationFrameworkCore",
    "ComparativeValidationReport",
    "ComparativeQualityFrameworkCore",
    "ComparativeQualityValidationRequest",
    "ComparativeQualityValidationResult",
    "ComparativeQualityReport",
    "ColumnCatalogAccessError",
    "DynamicColumnBuilderEngine",
    "DynamicRowBuilderEngine",
    "StructureCatalogAccessError",
]
