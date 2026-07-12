"""Pipeline interno del Módulo de Generación de Cuadros Comparativos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.dynamic_column_builder import DynamicColumnBuilder
from zovrake_motor.comparative_tables.components.dynamic_row_builder import DynamicRowBuilder
from zovrake_motor.comparative_tables.components.provider_organization_engine import (
    ProviderOrganizationEngine,
)
from zovrake_motor.comparative_tables.components.group_integrity_engine import GroupIntegrityEngine
from zovrake_motor.comparative_tables.components.traceability_metadata_engine import (
    TraceabilityMetadataEngine,
)
from zovrake_motor.comparative_tables.components.comparative_model_builder import (
    ComparativeModelBuilder,
)
from zovrake_motor.comparative_tables.components.comparative_validation_framework import (
    ComparativeValidationFramework,
)
from zovrake_motor.comparative_tables.components.comparative_quality_framework import (
    ComparativeQualityFramework,
)
from zovrake_motor.comparative_tables.components.comparative_structure_engine import (
    ComparativeStructureEngine,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildRequest,
    ComparativeStructureBuildResult,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeColumnBuildRequest,
    ComparativeColumnBuildResult,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildRequest,
    ComparativeRowBuildResult,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    ProviderOrganizationBuildRequest,
    ProviderOrganizationBuildResult,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityValidationRequest,
    GroupIntegrityValidationResult,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    TraceabilityMetadataEnrichmentRequest,
    TraceabilityMetadataEnrichmentResult,
)
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildRequest,
    ComparativeModelBuildResult,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationRequest,
    ComparativeModelValidationResult,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidationRequest,
    ComparativeQualityValidationResult,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.registry import ComponentRegistry

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration


@dataclass(frozen=True)
class ComparativeTablesPipelineStage:
    """Etapa del flujo de generación interno — referencia arquitectónica."""

    phase: ComparativeTablesPhase
    label: str
    order: int
    component_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "label": self.label,
            "order": self.order,
            "component_name": self.component_name,
        }


class ComparativeTablesPipeline:
    """
    Pipeline de generación de cuadros comparativos del módulo.

    El consumo del Modelo Comparativo de Dominio es la primera etapa funcional
    preparada del flujo.
    """

    DEFAULT_STAGES: tuple[ComparativeTablesPipelineStage, ...] = (
        ComparativeTablesPipelineStage(ComparativeTablesPhase.PREPARACION, "Preparación", 1),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.CONSUMO_MODELO_DOMINIO,
            "Consumo del Modelo Comparativo de Dominio",
            2,
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.ESTRUCTURA_COMPARATIVA,
            "Estructura Comparativa",
            3,
            "comparative_structure_engine",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.CONSTRUCCION_COLUMNAS,
            "Construcción de Columnas",
            4,
            "dynamic_column_builder",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.CONSTRUCCION_FILAS,
            "Construcción de Filas",
            5,
            "dynamic_row_builder",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.ORGANIZACION_PROVEEDORES,
            "Organización de Proveedores",
            6,
            "provider_organization_engine",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.INTEGRIDAD_GRUPOS,
            "Integridad de Grupos",
            7,
            "group_integrity_engine",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.TRAZABILIDAD_METADATOS,
            "Trazabilidad y Metadatos",
            8,
            "traceability_metadata_engine",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.MODELO_COMPARATIVO,
            "Modelo Comparativo",
            9,
            "comparative_model_builder",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.VALIDACION_COMPARATIVA,
            "Validación Comparativa",
            10,
            "comparative_validation_framework",
        ),
        ComparativeTablesPipelineStage(
            ComparativeTablesPhase.VALIDACION_CALIDAD,
            "Validación de Calidad",
            11,
            "comparative_quality_framework",
        ),
        ComparativeTablesPipelineStage(ComparativeTablesPhase.FINALIZACION, "Finalización", 12),
    )

    DOMAIN_MODEL_CONSUMPTION_STAGE = DEFAULT_STAGES[1]
    STRUCTURE_STAGE = DEFAULT_STAGES[2]
    COLUMN_BUILD_STAGE = DEFAULT_STAGES[3]
    ROW_BUILD_STAGE = DEFAULT_STAGES[4]
    PROVIDER_ORGANIZATION_STAGE = DEFAULT_STAGES[5]
    GROUP_INTEGRITY_STAGE = DEFAULT_STAGES[6]
    TRACEABILITY_STAGE = DEFAULT_STAGES[7]
    MODEL_BUILD_STAGE = DEFAULT_STAGES[8]
    VALIDATION_STAGE = DEFAULT_STAGES[9]
    QUALITY_STAGE = DEFAULT_STAGES[10]

    @classmethod
    def ordered_phases(cls) -> tuple[ComparativeTablesPhase, ...]:
        return tuple(stage.phase for stage in cls.DEFAULT_STAGES)

    @classmethod
    def domain_model_consumption_phase(cls) -> ComparativeTablesPhase:
        return cls.DOMAIN_MODEL_CONSUMPTION_STAGE.phase

    @classmethod
    def comparative_structure_phase(cls) -> ComparativeTablesPhase:
        return cls.STRUCTURE_STAGE.phase

    @classmethod
    def dynamic_column_build_phase(cls) -> ComparativeTablesPhase:
        return cls.COLUMN_BUILD_STAGE.phase

    @classmethod
    def dynamic_row_build_phase(cls) -> ComparativeTablesPhase:
        return cls.ROW_BUILD_STAGE.phase

    @classmethod
    def provider_organization_phase(cls) -> ComparativeTablesPhase:
        return cls.PROVIDER_ORGANIZATION_STAGE.phase

    @classmethod
    def group_integrity_phase(cls) -> ComparativeTablesPhase:
        return cls.GROUP_INTEGRITY_STAGE.phase

    @classmethod
    def traceability_metadata_phase(cls) -> ComparativeTablesPhase:
        return cls.TRACEABILITY_STAGE.phase

    @classmethod
    def comparative_model_build_phase(cls) -> ComparativeTablesPhase:
        return cls.MODEL_BUILD_STAGE.phase

    @classmethod
    def comparative_validation_phase(cls) -> ComparativeTablesPhase:
        return cls.VALIDATION_STAGE.phase

    @classmethod
    def comparative_quality_phase(cls) -> ComparativeTablesPhase:
        return cls.QUALITY_STAGE.phase

    @classmethod
    def build_snapshot(cls, registry: ComponentRegistry) -> list[dict[str, Any]]:
        snapshot: list[dict[str, Any]] = []
        for stage in cls.DEFAULT_STAGES:
            component = (
                registry.get(stage.component_name) if stage.component_name is not None else None
            )
            snapshot.append(
                {
                    **stage.to_dict(),
                    "component_registered": component is not None,
                    "component_ready": component.is_ready() if component is not None else False,
                }
            )
        return snapshot

    @classmethod
    def execute_comparative_structure_build(
        cls,
        registry: ComponentRegistry,
        request: ComparativeStructureBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> ComparativeStructureBuildResult:
        """Ejecuta la primera etapa funcional del PM6 — construcción de estructuras."""
        component = registry.get(cls.STRUCTURE_STAGE.component_name or "")
        if not isinstance(component, ComparativeStructureEngine):
            raise RuntimeError("Etapa de estructura comparativa no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Comparative Structure Engine no está preparado")
        return component.build(request, integration=integration)

    @classmethod
    def execute_dynamic_column_build(
        cls,
        registry: ComponentRegistry,
        request: ComparativeColumnBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> ComparativeColumnBuildResult:
        """Ejecuta la etapa de construcción de columnas dinámicas del PM6."""
        component = registry.get(cls.COLUMN_BUILD_STAGE.component_name or "")
        if not isinstance(component, DynamicColumnBuilder):
            raise RuntimeError("Etapa de construcción de columnas no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Dynamic Column Builder no está preparado")
        return component.build(request, integration=integration)

    @classmethod
    def execute_dynamic_row_build(
        cls,
        registry: ComponentRegistry,
        request: ComparativeRowBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> ComparativeRowBuildResult:
        """Ejecuta la etapa de construcción de filas dinámicas del PM6."""
        component = registry.get(cls.ROW_BUILD_STAGE.component_name or "")
        if not isinstance(component, DynamicRowBuilder):
            raise RuntimeError("Etapa de construcción de filas no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Dynamic Row Builder no está preparado")
        return component.build(request, integration=integration)

    @classmethod
    def execute_provider_organization(
        cls,
        registry: ComponentRegistry,
        request: ProviderOrganizationBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> ProviderOrganizationBuildResult:
        """Ejecuta la etapa de organización de proveedores del PM6."""
        component = registry.get(cls.PROVIDER_ORGANIZATION_STAGE.component_name or "")
        if not isinstance(component, ProviderOrganizationEngine):
            raise RuntimeError(
                "Etapa de organización de proveedores no disponible en el Pipeline",
            )
        if not component.is_ready():
            raise RuntimeError("Provider Organization Engine no está preparado")
        return component.organize(request, integration=integration)

    @classmethod
    def execute_group_integrity_validation(
        cls,
        registry: ComponentRegistry,
        request: GroupIntegrityValidationRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> GroupIntegrityValidationResult:
        """Ejecuta la etapa de validación de integridad de grupos del PM6."""
        component = registry.get(cls.GROUP_INTEGRITY_STAGE.component_name or "")
        if not isinstance(component, GroupIntegrityEngine):
            raise RuntimeError(
                "Etapa de integridad de grupos no disponible en el Pipeline",
            )
        if not component.is_ready():
            raise RuntimeError("Group Integrity Engine no está preparado")
        return component.validate(request, integration=integration)

    @classmethod
    def execute_traceability_metadata_enrichment(
        cls,
        registry: ComponentRegistry,
        request: TraceabilityMetadataEnrichmentRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> TraceabilityMetadataEnrichmentResult:
        """Ejecuta la etapa de enriquecimiento de trazabilidad y metadatos del PM6."""
        component = registry.get(cls.TRACEABILITY_STAGE.component_name or "")
        if not isinstance(component, TraceabilityMetadataEngine):
            raise RuntimeError(
                "Etapa de trazabilidad y metadatos no disponible en el Pipeline",
            )
        if not component.is_ready():
            raise RuntimeError("Traceability & Metadata Engine no está preparado")
        return component.enrich(request, integration=integration)

    @classmethod
    def execute_comparative_model_build(
        cls,
        registry: ComponentRegistry,
        request: ComparativeModelBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> ComparativeModelBuildResult:
        """Ejecuta la etapa de construcción del Modelo Comparativo Definitivo del PM6."""
        component = registry.get(cls.MODEL_BUILD_STAGE.component_name or "")
        if not isinstance(component, ComparativeModelBuilder):
            raise RuntimeError(
                "Etapa de modelo comparativo no disponible en el Pipeline",
            )
        if not component.is_ready():
            raise RuntimeError("Comparative Model Builder no está preparado")
        return component.build(request, integration=integration)

    @classmethod
    def execute_comparative_model_validation(
        cls,
        registry: ComponentRegistry,
        request: ComparativeModelValidationRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> ComparativeModelValidationResult:
        """Ejecuta la etapa de validación del Modelo Comparativo Definitivo del PM6."""
        component = registry.get(cls.VALIDATION_STAGE.component_name or "")
        if not isinstance(component, ComparativeValidationFramework):
            raise RuntimeError(
                "Etapa de validación comparativa no disponible en el Pipeline",
            )
        if not component.is_ready():
            raise RuntimeError("Comparative Validation Framework no está preparado")
        return component.validate(request, integration=integration)

    @classmethod
    def execute_comparative_quality_audit(
        cls,
        registry: ComponentRegistry,
        request: ComparativeQualityValidationRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
    ) -> ComparativeQualityValidationResult:
        """Ejecuta la etapa de auditoría de calidad del PM6."""
        component = registry.get(cls.QUALITY_STAGE.component_name or "")
        if not isinstance(component, ComparativeQualityFramework):
            raise RuntimeError(
                "Etapa de validación de calidad no disponible en el Pipeline",
            )
        if not component.is_ready():
            raise RuntimeError("Comparative Quality Framework no está preparado")
        return component.audit(request, integration=integration)
