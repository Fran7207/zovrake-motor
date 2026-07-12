"""Servicio del Módulo de Generación de Cuadros Comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.comparative_structure_engine import (
    ComparativeStructureEngine,
)
from zovrake_motor.comparative_tables.components.comparative_tables_coordinator import (
    ComparativeTablesCoordinator,
)
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
from zovrake_motor.comparative_tables.input_gateway import ClassificationOutputGateway
from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
from zovrake_motor.comparative_tables.models import ComparativeTablesRequest, ComparativeTablesResult
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.comparative_tables.port import ComparativeTablesPort
from zovrake_motor.comparative_tables.registry import ComponentRegistry
from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.events.manager import EventManager
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeTablesService(ConfigurationAccessible, ModulePort, ComparativeTablesPort):
    """
    Módulo de Generación de Cuadros Comparativos.

    Responsabilidad única: transformar el Modelo Comparativo de Dominio en
    modelos de cuadros comparativos dinámicos para representación futura.
    """

    MODULE_NAME = "comparative_tables"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
        component_registry: ComponentRegistry | None = None,
        integration: ComparativeTablesMotorIntegration | None = None,
        classification_gateway: ClassificationOutputGateway | None = None,
    ) -> None:
        super().__init__(config_provider=config_provider)
        self._integration = integration or ComparativeTablesMotorIntegration(
            config_provider=config_provider,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        self._registry = component_registry or ComponentRegistry()
        self._comparative_tables_coordinator: ComparativeTablesCoordinator | None = None
        self._classification_gateway = classification_gateway
        self._initialized = False

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    @property
    def component_registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def comparative_tables_coordinator(self) -> ComparativeTablesCoordinator | None:
        return self._comparative_tables_coordinator

    @property
    def classification_gateway(self) -> ClassificationOutputGateway:
        if self._classification_gateway is None:
            self._classification_gateway = ClassificationOutputGateway(
                settings=self._integration.comparative_tables_settings(),
            )
        return self._classification_gateway

    @property
    def integration(self) -> ComparativeTablesMotorIntegration:
        return self._integration

    @property
    def state_manager(self) -> StateManager:
        return self._integration.state_manager

    @property
    def event_manager(self) -> EventManager:
        return self._integration.event_manager

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._comparative_tables_coordinator = self._registry.register_defaults(
            config_provider=self._config_provider,
        )
        structure_component = self._registry.get("comparative_structure_engine")
        if isinstance(structure_component, ComparativeStructureEngine):
            structure_component.initialize()
        column_component = self._registry.get("dynamic_column_builder")
        if isinstance(column_component, DynamicColumnBuilder):
            column_component.initialize()
        row_component = self._registry.get("dynamic_row_builder")
        if isinstance(row_component, DynamicRowBuilder):
            row_component.initialize()
        poe_component = self._registry.get("provider_organization_engine")
        if isinstance(poe_component, ProviderOrganizationEngine):
            poe_component.initialize()
        gie_component = self._registry.get("group_integrity_engine")
        if isinstance(gie_component, GroupIntegrityEngine):
            gie_component.initialize()
        tme_component = self._registry.get("traceability_metadata_engine")
        if isinstance(tme_component, TraceabilityMetadataEngine):
            tme_component.initialize()
        cmb_component = self._registry.get("comparative_model_builder")
        if isinstance(cmb_component, ComparativeModelBuilder):
            cmb_component.initialize()
        cvf_component = self._registry.get("comparative_validation_framework")
        if isinstance(cvf_component, ComparativeValidationFramework):
            cvf_component.initialize()
        cqf_component = self._registry.get("comparative_quality_framework")
        if isinstance(cqf_component, ComparativeQualityFramework):
            cqf_component.initialize()
        self._classification_gateway = ClassificationOutputGateway(
            settings=self._integration.comparative_tables_settings(),
        )
        self._initialized = True

    @property
    def comparative_structure_engine(self):
        component = self._registry.get("comparative_structure_engine")
        if isinstance(component, ComparativeStructureEngine):
            return component.engine
        return None

    @property
    def dynamic_column_builder(self):
        component = self._registry.get("dynamic_column_builder")
        if isinstance(component, DynamicColumnBuilder):
            return component.engine
        return None

    @property
    def dynamic_row_builder(self):
        component = self._registry.get("dynamic_row_builder")
        if isinstance(component, DynamicRowBuilder):
            return component.engine
        return None

    @property
    def provider_organization_engine(self):
        component = self._registry.get("provider_organization_engine")
        if isinstance(component, ProviderOrganizationEngine):
            return component.engine
        return None

    @property
    def group_integrity_engine(self):
        component = self._registry.get("group_integrity_engine")
        if isinstance(component, GroupIntegrityEngine):
            return component.engine
        return None

    @property
    def traceability_metadata_engine(self):
        component = self._registry.get("traceability_metadata_engine")
        if isinstance(component, TraceabilityMetadataEngine):
            return component.engine
        return None

    @property
    def comparative_model_builder(self):
        component = self._registry.get("comparative_model_builder")
        if isinstance(component, ComparativeModelBuilder):
            return component.engine
        return None

    @property
    def comparative_validation_framework(self):
        component = self._registry.get("comparative_validation_framework")
        if isinstance(component, ComparativeValidationFramework):
            return component.engine
        return None

    @property
    def comparative_quality_framework(self):
        component = self._registry.get("comparative_quality_framework")
        if isinstance(component, ComparativeQualityFramework):
            return component.engine
        return None

    def build_comparative_structure(
        self,
        request: ComparativeStructureBuildRequest,
    ) -> ComparativeStructureBuildResult:
        return ComparativeTablesPipeline.execute_comparative_structure_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_dynamic_columns(
        self,
        request: ComparativeColumnBuildRequest,
    ) -> ComparativeColumnBuildResult:
        return ComparativeTablesPipeline.execute_dynamic_column_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_dynamic_rows(
        self,
        request: ComparativeRowBuildRequest,
    ) -> ComparativeRowBuildResult:
        return ComparativeTablesPipeline.execute_dynamic_row_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def organize_providers(
        self,
        request: ProviderOrganizationBuildRequest,
    ) -> ProviderOrganizationBuildResult:
        return ComparativeTablesPipeline.execute_provider_organization(
            self._registry,
            request,
            integration=self._integration,
        )

    def validate_group_integrity(
        self,
        request: GroupIntegrityValidationRequest,
    ) -> GroupIntegrityValidationResult:
        return ComparativeTablesPipeline.execute_group_integrity_validation(
            self._registry,
            request,
            integration=self._integration,
        )

    def enrich_traceability_metadata(
        self,
        request: TraceabilityMetadataEnrichmentRequest,
    ) -> TraceabilityMetadataEnrichmentResult:
        return ComparativeTablesPipeline.execute_traceability_metadata_enrichment(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_comparative_model(
        self,
        request: ComparativeModelBuildRequest,
    ) -> ComparativeModelBuildResult:
        return ComparativeTablesPipeline.execute_comparative_model_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def validate_comparative_model(
        self,
        request: ComparativeModelValidationRequest,
    ) -> ComparativeModelValidationResult:
        return ComparativeTablesPipeline.execute_comparative_model_validation(
            self._registry,
            request,
            integration=self._integration,
        )

    def audit_comparative_quality(
        self,
        request: ComparativeQualityValidationRequest,
    ) -> ComparativeQualityValidationResult:
        return ComparativeTablesPipeline.execute_comparative_quality_audit(
            self._registry,
            request,
            integration=self._integration,
        )

    def prepare(self, request: ComparativeTablesRequest) -> ComparativeTablesResult:
        settings = self._integration.comparative_tables_settings()
        gateway = self.classification_gateway
        input_bundle = request.input_bundle()
        consumption = gateway.prepare_consumption(input_bundle)

        structure_engine = self.comparative_structure_engine
        column_engine = self.dynamic_column_builder
        row_engine = self.dynamic_row_builder
        poe_engine = self.provider_organization_engine
        gie_engine = self.group_integrity_engine
        tme_engine = self.traceability_metadata_engine
        cmb_engine = self.comparative_model_builder
        cvf_engine = self.comparative_validation_framework
        cqf_engine = self.comparative_quality_framework

        return ComparativeTablesResult(
            process_id=request.process_id,
            prepared=True,
            message="Arquitectura de Generación de Cuadros Comparativos preparada — sin procesamiento",
            components_ready=self._registry.ready_count(),
            metadata={
                "codigo_req": request.codigo_req,
                "enabled": settings.enabled,
                "components_count": self._registry.count(),
                "classification_consumption": consumption,
                "pm6_output_contract_required": settings.pm6_output_contract_required,
                "structure_builders_registered": (
                    structure_engine.registry.count() if structure_engine else 0
                ),
                "structure_catalog_entries_count": (
                    structure_engine.catalog_store.count() if structure_engine else 0
                ),
                "column_builders_registered": (
                    column_engine.registry.count() if column_engine else 0
                ),
                "column_catalog_entries_count": (
                    column_engine.catalog_store.count() if column_engine else 0
                ),
                "row_builders_registered": (
                    row_engine.registry.count() if row_engine else 0
                ),
                "row_catalog_entries_count": (
                    row_engine.catalog_store.count() if row_engine else 0
                ),
                "provider_organizers_registered": (
                    poe_engine.registry.count() if poe_engine else 0
                ),
                "provider_catalog_entries_count": (
                    poe_engine.catalog_store.count() if poe_engine else 0
                ),
                "integrity_validators_registered": (
                    gie_engine.registry.count() if gie_engine else 0
                ),
                "integrity_report_entries_count": (
                    gie_engine.report_store.count() if gie_engine else 0
                ),
                "metadata_enrichers_registered": (
                    tme_engine.registry.count() if tme_engine else 0
                ),
                "enriched_catalog_entries_count": (
                    tme_engine.catalog_store.count() if tme_engine else 0
                ),
                "model_builders_registered": (
                    cmb_engine.registry.count() if cmb_engine else 0
                ),
                "definitive_model_catalog_entries_count": (
                    cmb_engine.catalog_store.count() if cmb_engine else 0
                ),
                "model_validators_registered": (
                    cvf_engine.registry.count() if cvf_engine else 0
                ),
                "validation_report_entries_count": (
                    cvf_engine.report_store.count() if cvf_engine else 0
                ),
                "quality_validators_registered": (
                    cqf_engine.registry.count() if cqf_engine else 0
                ),
                "quality_report_entries_count": (
                    cqf_engine.report_store.count() if cqf_engine else 0
                ),
                "comparative_tables_pipeline": ComparativeTablesPipeline.build_snapshot(self._registry),
            },
        )

    def get_comparative_tables_pipeline_snapshot(self) -> list[dict[str, Any]]:
        return ComparativeTablesPipeline.build_snapshot(self._registry)

    def snapshot(self) -> dict[str, Any]:
        structure_engine = self.comparative_structure_engine
        column_engine = self.dynamic_column_builder
        row_engine = self.dynamic_row_builder
        poe_engine = self.provider_organization_engine
        gie_engine = self.group_integrity_engine
        tme_engine = self.traceability_metadata_engine
        cmb_engine = self.comparative_model_builder
        cvf_engine = self.comparative_validation_framework
        cqf_engine = self.comparative_quality_framework
        return {
            "module_name": self.MODULE_NAME,
            "initialized": self._initialized,
            "integration": self._integration.snapshot(),
            "classification_gateway": self.classification_gateway.snapshot(),
            "components": self._registry.snapshot(),
            "comparative_tables_coordinator": (
                self._comparative_tables_coordinator.snapshot()
                if self._comparative_tables_coordinator is not None
                else None
            ),
            "comparative_structure_engine": (
                structure_engine.snapshot() if structure_engine is not None else None
            ),
            "dynamic_column_builder": (
                column_engine.snapshot() if column_engine is not None else None
            ),
            "dynamic_row_builder": (
                row_engine.snapshot() if row_engine is not None else None
            ),
            "provider_organization_engine": (
                poe_engine.snapshot() if poe_engine is not None else None
            ),
            "group_integrity_engine": (
                gie_engine.snapshot() if gie_engine is not None else None
            ),
            "traceability_metadata_engine": (
                tme_engine.snapshot() if tme_engine is not None else None
            ),
            "comparative_model_builder": (
                cmb_engine.snapshot() if cmb_engine is not None else None
            ),
            "comparative_validation_framework": (
                cvf_engine.snapshot() if cvf_engine is not None else None
            ),
            "comparative_quality_framework": (
                cqf_engine.snapshot() if cqf_engine is not None else None
            ),
            "comparative_tables_pipeline": self.get_comparative_tables_pipeline_snapshot(),
        }
