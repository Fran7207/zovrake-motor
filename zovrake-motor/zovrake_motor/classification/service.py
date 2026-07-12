"""Servicio del Módulo de Clasificación Inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.classification_coordinator import ClassificationCoordinator
from zovrake_motor.classification.components.concept_analysis_engine import ConceptAnalysisEngineComponent
from zovrake_motor.classification.components.material_classification_engine import (
    MaterialClassificationEngineComponent,
)
from zovrake_motor.classification.components.concept_normalization_engine import (
    ConceptNormalizationEngineComponent,
)
from zovrake_motor.classification.components.service_classification_engine import (
    ServiceClassificationEngineComponent,
)
from zovrake_motor.classification.concept_analysis.models import ConceptAnalysisRequest, ConceptAnalysisResult
from zovrake_motor.classification.components.comparable_group_builder import ComparableGroupBuilder
from zovrake_motor.classification.components.context_association_engine import ContextAssociationEngineComponent
from zovrake_motor.classification.components.comparative_domain_model_builder import (
    ComparativeDomainModelBuilder,
)
from zovrake_motor.classification.components.classification_quality_framework import (
    ClassificationQualityFramework,
)
from zovrake_motor.classification.components.equivalence_detection_engine import (
    EquivalenceDetectionEngineComponent,
)
from zovrake_motor.classification.comparable_group_builder.models import (
    ComparableGroupBuildRequest,
    ComparableGroupBuildResult,
)
from zovrake_motor.classification.context_association.models import (
    ContextAssociationRequest,
    ContextAssociationResult,
)
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainModelBuildRequest,
    ComparativeDomainModelBuildResult,
)
from zovrake_motor.classification.classification_quality.models import (
    ClassificationQualityValidationRequest,
    ClassificationQualityValidationResult,
)
from zovrake_motor.classification.concept_normalization.models import (
    ConceptNormalizationRequest,
    ConceptNormalizationResult,
)
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceDetectionRequest,
    EquivalenceDetectionResult,
)
from zovrake_motor.classification.material_classification.models import (
    MaterialClassificationRequest,
    MaterialClassificationResult,
)
from zovrake_motor.classification.service_classification.models import (
    ServiceClassificationRequest,
    ServiceClassificationResult,
)
from zovrake_motor.classification.input_gateway import ComprehensionOutputGateway
from zovrake_motor.classification.integration import ClassificationMotorIntegration
from zovrake_motor.classification.models import ClassificationRequest, ClassificationResult
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.classification.port import ClassificationPort
from zovrake_motor.classification.registry import ComponentRegistry
from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.events.manager import EventManager
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ClassificationService(ConfigurationAccessible, ModulePort, ClassificationPort):
    """
    Módulo de Clasificación Inteligente.

    Responsabilidad única: organizar la información estructurada producida
    por Comprensión Documental para futuros grupos comparables.
    """

    MODULE_NAME = "classification"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
        component_registry: ComponentRegistry | None = None,
        integration: ClassificationMotorIntegration | None = None,
        comprehension_gateway: ComprehensionOutputGateway | None = None,
    ) -> None:
        super().__init__(config_provider=config_provider)
        self._integration = integration or ClassificationMotorIntegration(
            config_provider=config_provider,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        self._registry = component_registry or ComponentRegistry()
        self._classification_coordinator: ClassificationCoordinator | None = None
        self._comprehension_gateway = comprehension_gateway
        self._initialized = False

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    @property
    def component_registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def classification_coordinator(self) -> ClassificationCoordinator | None:
        return self._classification_coordinator

    @property
    def concept_analysis_engine(self):
        component = self._registry.get("concept_analysis_engine")
        if isinstance(component, ConceptAnalysisEngineComponent):
            return component.engine
        return None

    @property
    def material_classification_engine(self):
        component = self._registry.get("material_classification_engine")
        if isinstance(component, MaterialClassificationEngineComponent):
            return component.engine
        return None

    @property
    def service_classification_engine(self):
        component = self._registry.get("service_classification_engine")
        if isinstance(component, ServiceClassificationEngineComponent):
            return component.engine
        return None

    @property
    def concept_normalization_engine(self):
        component = self._registry.get("concept_normalization_engine")
        if isinstance(component, ConceptNormalizationEngineComponent):
            return component.engine
        return None

    @property
    def equivalence_detection_engine(self):
        component = self._registry.get("equivalence_detection_engine")
        if isinstance(component, EquivalenceDetectionEngineComponent):
            return component.engine
        return None

    @property
    def comparable_group_builder(self):
        component = self._registry.get("comparable_group_builder")
        if isinstance(component, ComparableGroupBuilder):
            return component.engine
        return None

    @property
    def context_association_engine(self):
        component = self._registry.get("context_association_engine")
        if isinstance(component, ContextAssociationEngineComponent):
            return component.engine
        return None

    @property
    def comparative_domain_model_builder(self):
        component = self._registry.get("comparative_domain_model_builder")
        if isinstance(component, ComparativeDomainModelBuilder):
            return component.engine
        return None

    @property
    def classification_quality_framework(self):
        component = self._registry.get("classification_quality_framework")
        if isinstance(component, ClassificationQualityFramework):
            return component.engine
        return None

    @property
    def comprehension_gateway(self) -> ComprehensionOutputGateway:
        if self._comprehension_gateway is None:
            self._comprehension_gateway = ComprehensionOutputGateway(
                settings=self._integration.classification_settings(),
            )
        return self._comprehension_gateway

    @property
    def integration(self) -> ClassificationMotorIntegration:
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
        self._classification_coordinator = self._registry.register_defaults(
            config_provider=self._config_provider,
        )
        concept_component = self._registry.get("concept_analysis_engine")
        if isinstance(concept_component, ConceptAnalysisEngineComponent):
            concept_component.initialize()
        material_component = self._registry.get("material_classification_engine")
        if isinstance(material_component, MaterialClassificationEngineComponent):
            material_component.initialize()
        service_component = self._registry.get("service_classification_engine")
        if isinstance(service_component, ServiceClassificationEngineComponent):
            service_component.initialize()
        normalization_component = self._registry.get("concept_normalization_engine")
        if isinstance(normalization_component, ConceptNormalizationEngineComponent):
            normalization_component.initialize()
        equivalence_component = self._registry.get("equivalence_detection_engine")
        if isinstance(equivalence_component, EquivalenceDetectionEngineComponent):
            equivalence_component.initialize()
        comparable_group_component = self._registry.get("comparable_group_builder")
        if isinstance(comparable_group_component, ComparableGroupBuilder):
            comparable_group_component.initialize()
        context_association_component = self._registry.get("context_association_engine")
        if isinstance(context_association_component, ContextAssociationEngineComponent):
            context_association_component.initialize()
        comparative_domain_component = self._registry.get("comparative_domain_model_builder")
        if isinstance(comparative_domain_component, ComparativeDomainModelBuilder):
            comparative_domain_component.initialize()
        quality_component = self._registry.get("classification_quality_framework")
        if isinstance(quality_component, ClassificationQualityFramework):
            quality_component.initialize()
        self._comprehension_gateway = ComprehensionOutputGateway(
            settings=self._integration.classification_settings(),
        )
        self._initialized = True

    def analyze_concepts(self, request: ConceptAnalysisRequest) -> ConceptAnalysisResult:
        return ClassificationPipeline.execute_concept_analysis(
            self._registry,
            request,
            integration=self._integration,
        )

    def classify_materials(self, request: MaterialClassificationRequest) -> MaterialClassificationResult:
        return ClassificationPipeline.execute_material_classification(
            self._registry,
            request,
            integration=self._integration,
        )

    def classify_services(self, request: ServiceClassificationRequest) -> ServiceClassificationResult:
        return ClassificationPipeline.execute_service_classification(
            self._registry,
            request,
            integration=self._integration,
        )

    def normalize_concepts(self, request: ConceptNormalizationRequest) -> ConceptNormalizationResult:
        return ClassificationPipeline.execute_concept_normalization(
            self._registry,
            request,
            integration=self._integration,
        )

    def detect_equivalences(self, request: EquivalenceDetectionRequest) -> EquivalenceDetectionResult:
        return ClassificationPipeline.execute_equivalence_detection(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_comparable_groups(
        self,
        request: ComparableGroupBuildRequest,
    ) -> ComparableGroupBuildResult:
        return ClassificationPipeline.execute_comparable_group_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def associate_context(self, request: ContextAssociationRequest) -> ContextAssociationResult:
        return ClassificationPipeline.execute_context_association(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_comparative_domain_model(
        self,
        request: ComparativeDomainModelBuildRequest,
    ) -> ComparativeDomainModelBuildResult:
        return ClassificationPipeline.execute_comparative_domain_model_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def validate_classification_quality(
        self,
        request: ClassificationQualityValidationRequest,
    ) -> ClassificationQualityValidationResult:
        return ClassificationPipeline.execute_quality_validation(
            self._registry,
            request,
            integration=self._integration,
        )

    def prepare(self, request: ClassificationRequest) -> ClassificationResult:
        settings = self._integration.classification_settings()
        gateway = self.comprehension_gateway
        input_bundle = request.input_bundle()
        consumption = gateway.prepare_consumption(input_bundle)
        concept_engine = self.concept_analysis_engine
        material_engine = self.material_classification_engine
        service_engine = self.service_classification_engine
        normalization_engine = self.concept_normalization_engine
        equivalence_engine = self.equivalence_detection_engine
        comparable_group_builder = self.comparable_group_builder
        context_association_engine = self.context_association_engine
        comparative_domain_model_builder = self.comparative_domain_model_builder
        classification_quality_framework = self.classification_quality_framework

        return ClassificationResult(
            process_id=request.process_id,
            prepared=True,
            message="Arquitectura de Clasificación Inteligente preparada — sin procesamiento",
            components_ready=self._registry.ready_count(),
            metadata={
                "codigo_req": request.codigo_req,
                "enabled": settings.enabled,
                "components_count": self._registry.count(),
                "comprehension_consumption": consumption,
                "concept_detectors_registered": concept_engine.registry.count() if concept_engine else 0,
                "concept_catalog_entries_count": concept_engine.catalog_store.count() if concept_engine else 0,
                "material_classifiers_registered": material_engine.registry.count() if material_engine else 0,
                "material_catalog_entries_count": material_engine.catalog_store.count() if material_engine else 0,
                "service_classifiers_registered": service_engine.registry.count() if service_engine else 0,
                "service_catalog_entries_count": service_engine.catalog_store.count() if service_engine else 0,
                "concept_normalizers_registered": (
                    normalization_engine.registry.count() if normalization_engine else 0
                ),
                "normalized_catalog_entries_count": (
                    normalization_engine.catalog_store.count() if normalization_engine else 0
                ),
                "equivalence_detectors_registered": (
                    equivalence_engine.registry.count() if equivalence_engine else 0
                ),
                "equivalence_catalog_entries_count": (
                    equivalence_engine.catalog_store.count() if equivalence_engine else 0
                ),
                "group_builders_registered": (
                    comparable_group_builder.registry.count() if comparable_group_builder else 0
                ),
                "comparable_group_catalog_entries_count": (
                    comparable_group_builder.catalog_store.count() if comparable_group_builder else 0
                ),
                "context_associators_registered": (
                    context_association_engine.registry.count() if context_association_engine else 0
                ),
                "context_association_catalog_entries_count": (
                    context_association_engine.catalog_store.count() if context_association_engine else 0
                ),
                "domain_model_builders_registered": (
                    comparative_domain_model_builder.registry.count()
                    if comparative_domain_model_builder
                    else 0
                ),
                "comparative_domain_model_catalog_entries_count": (
                    comparative_domain_model_builder.catalog_store.count()
                    if comparative_domain_model_builder
                    else 0
                ),
                "quality_validators_registered": (
                    classification_quality_framework.registry.count()
                    if classification_quality_framework
                    else 0
                ),
                "quality_report_entries_count": (
                    classification_quality_framework.report_store.count()
                    if classification_quality_framework
                    else 0
                ),
                "classification_pipeline": ClassificationPipeline.build_snapshot(self._registry),
            },
        )

    def get_classification_pipeline_snapshot(self) -> list[dict[str, Any]]:
        return ClassificationPipeline.build_snapshot(self._registry)

    def snapshot(self) -> dict[str, Any]:
        concept_engine = self.concept_analysis_engine
        material_engine = self.material_classification_engine
        service_engine = self.service_classification_engine
        normalization_engine = self.concept_normalization_engine
        equivalence_engine = self.equivalence_detection_engine
        comparable_group_builder = self.comparable_group_builder
        context_association_engine = self.context_association_engine
        comparative_domain_model_builder = self.comparative_domain_model_builder
        classification_quality_framework = self.classification_quality_framework
        return {
            "module_name": self.MODULE_NAME,
            "initialized": self._initialized,
            "integration": self._integration.snapshot(),
            "comprehension_gateway": self.comprehension_gateway.snapshot(),
            "components": self._registry.snapshot(),
            "classification_coordinator": (
                self._classification_coordinator.snapshot()
                if self._classification_coordinator is not None
                else None
            ),
            "concept_analysis_engine": concept_engine.snapshot() if concept_engine is not None else None,
            "material_classification_engine": (
                material_engine.snapshot() if material_engine is not None else None
            ),
            "service_classification_engine": (
                service_engine.snapshot() if service_engine is not None else None
            ),
            "concept_normalization_engine": (
                normalization_engine.snapshot() if normalization_engine is not None else None
            ),
            "equivalence_detection_engine": (
                equivalence_engine.snapshot() if equivalence_engine is not None else None
            ),
            "comparable_group_builder": (
                comparable_group_builder.snapshot() if comparable_group_builder is not None else None
            ),
            "context_association_engine": (
                context_association_engine.snapshot() if context_association_engine is not None else None
            ),
            "comparative_domain_model_builder": (
                comparative_domain_model_builder.snapshot()
                if comparative_domain_model_builder is not None
                else None
            ),
            "classification_quality_framework": (
                classification_quality_framework.snapshot()
                if classification_quality_framework is not None
                else None
            ),
            "classification_pipeline": self.get_classification_pipeline_snapshot(),
        }
