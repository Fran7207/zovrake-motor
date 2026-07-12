"""Servicio del Módulo de Comprensión Documental."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.adapters import DocumentAdaptersManager
from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationRequest, CanonicalRepresentationResult
from zovrake_motor.comprehension.components.extractors import ExtractorsRegistry
from zovrake_motor.comprehension.components.document_coordinator import DocumentCoordinator
from zovrake_motor.comprehension.components.format_identifier import FormatIdentifier
from zovrake_motor.comprehension.components.document_index import DocumentIndex
from zovrake_motor.comprehension.components.context_manager import DocumentContextManager
from zovrake_motor.comprehension.components.model_builder import InternalModelBuilder
from zovrake_motor.comprehension.components.normalizer import ContentNormalizer
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest, InternalModelBuildResult
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest, DocumentIndexResult
from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest, ContextIntegrationResult
from zovrake_motor.comprehension.components.validator import DocumentValidator
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ContentExtractionResult
from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
from zovrake_motor.comprehension.models import ComprehensionRequest, ComprehensionResult
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.comprehension.port import ComprehensionPort
from zovrake_motor.comprehension.registry import ComponentRegistry
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, DocumentRecognitionResult
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, DocumentValidationResult
from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.events.manager import EventManager
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComprehensionService(ConfigurationAccessible, ModulePort, ComprehensionPort):
    """
    Módulo de Comprensión Documental.

    Responsabilidad única: administrar la arquitectura base para comprender
    documentos enviados desde el Centro de Evidencias.

    Sin lectura, OCR, extracción ni lógica de negocio en esta etapa.
    """

    MODULE_NAME = "comprehension"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
        component_registry: ComponentRegistry | None = None,
        integration: ComprehensionMotorIntegration | None = None,
    ) -> None:
        super().__init__(config_provider=config_provider)
        self._integration = integration or ComprehensionMotorIntegration(
            config_provider=config_provider,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        self._registry = component_registry or ComponentRegistry()
        self._document_coordinator: DocumentCoordinator | None = None
        self._initialized = False

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    @property
    def component_registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def document_coordinator(self) -> DocumentCoordinator | None:
        return self._document_coordinator

    @property
    def validation_framework(self):
        validator = self._registry.get("document_validator")
        if isinstance(validator, DocumentValidator):
            return validator.framework
        return None

    @property
    def recognition_engine(self):
        identifier = self._registry.get("format_identifier")
        if isinstance(identifier, FormatIdentifier):
            return identifier.engine
        return None

    @property
    def adapter_framework(self):
        adapters = self._registry.get("document_adapters")
        if isinstance(adapters, DocumentAdaptersManager):
            return adapters.framework
        return None

    @property
    def extraction_engine(self):
        extractors = self._registry.get("extractors")
        if isinstance(extractors, ExtractorsRegistry):
            return extractors.engine
        return None

    @property
    def canonical_engine(self):
        normalizer = self._registry.get("normalizer")
        if isinstance(normalizer, ContentNormalizer):
            return normalizer.engine
        return None

    @property
    def internal_model_builder(self):
        builder = self._registry.get("internal_model_builder")
        if isinstance(builder, InternalModelBuilder):
            return builder.engine
        return None

    @property
    def knowledge_index(self):
        index = self._registry.get("document_index")
        if isinstance(index, DocumentIndex):
            return index.engine
        return None

    @property
    def document_knowledge_index(self):
        return self.knowledge_index

    @property
    def context_integration_engine(self):
        manager = self._registry.get("context_manager")
        if isinstance(manager, DocumentContextManager):
            return manager.engine
        return None

    @property
    def context_integration(self):
        return self.context_integration_engine

    @property
    def integration(self) -> ComprehensionMotorIntegration:
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
        self._document_coordinator = self._registry.register_defaults(
            config_provider=self._config_provider,
        )
        validator = self._registry.get("document_validator")
        if isinstance(validator, DocumentValidator):
            validator.initialize()
        adapters = self._registry.get("document_adapters")
        if isinstance(adapters, DocumentAdaptersManager):
            adapters.initialize()
        identifier = self._registry.get("format_identifier")
        if isinstance(identifier, FormatIdentifier):
            identifier.initialize()
        extractors = self._registry.get("extractors")
        if isinstance(extractors, ExtractorsRegistry):
            extractors.initialize()
        normalizer = self._registry.get("normalizer")
        if isinstance(normalizer, ContentNormalizer):
            normalizer.initialize()
        model_builder = self._registry.get("internal_model_builder")
        if isinstance(model_builder, InternalModelBuilder):
            model_builder.initialize()
        document_index = self._registry.get("document_index")
        if isinstance(document_index, DocumentIndex):
            document_index.initialize()
        context_manager = self._registry.get("context_manager")
        if isinstance(context_manager, DocumentContextManager):
            context_manager.initialize()
        self._initialized = True

    def validate_document(self, request: DocumentValidationRequest) -> DocumentValidationResult:
        return DocumentComprehensionPipeline.execute_validation(
            self._registry,
            request,
            integration=self._integration,
        )

    def recognize_document(self, request: DocumentRecognitionRequest) -> DocumentRecognitionResult:
        return DocumentComprehensionPipeline.execute_recognition(
            self._registry,
            request,
            integration=self._integration,
            adapter_framework=self.adapter_framework,
        )

    def extract_content(self, request: ContentExtractionRequest) -> ContentExtractionResult:
        return DocumentComprehensionPipeline.execute_extraction(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_canonical_representation(
        self,
        request: CanonicalRepresentationRequest,
    ) -> CanonicalRepresentationResult:
        return DocumentComprehensionPipeline.execute_canonical_representation(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_internal_model(self, request: InternalModelBuildRequest) -> InternalModelBuildResult:
        return DocumentComprehensionPipeline.execute_internal_model_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def index_document(self, request: DocumentIndexRequest) -> DocumentIndexResult:
        return DocumentComprehensionPipeline.execute_indexing(
            self._registry,
            request,
            integration=self._integration,
        )

    def integrate_context(self, request: ContextIntegrationRequest) -> ContextIntegrationResult:
        return DocumentComprehensionPipeline.execute_context_integration(
            self._registry,
            request,
            integration=self._integration,
        )

    def prepare(self, request: ComprehensionRequest) -> ComprehensionResult:
        settings = self._integration.comprehension_settings()
        adapter_fw = self.adapter_framework
        validation = self.validation_framework
        recognition = self.recognition_engine
        extraction = self.extraction_engine
        canonical = self.canonical_engine
        internal_model = self.internal_model_builder
        knowledge_index = self.knowledge_index
        context_integration = self.context_integration_engine
        return ComprehensionResult(
            process_id=request.process_id,
            prepared=True,
            message="Arquitectura de Comprensión Documental preparada — sin procesamiento",
            components_ready=self._registry.ready_count(),
            metadata={
                "codigo_req": request.codigo_req,
                "enabled": settings.enabled,
                "supported_formats": list(settings.supported_formats),
                "components_count": self._registry.count(),
                "validation_rules_registered": validation.registry.count() if validation else 0,
                "recognition_strategies_registered": recognition.registry.count() if recognition else 0,
                "extractors_registered": extraction.registry.count() if extraction else 0,
                "canonical_transformers_registered": canonical.registry.count() if canonical else 0,
                "internal_model_builders_registered": internal_model.registry.count() if internal_model else 0,
                "knowledge_index_entries_count": knowledge_index.store.count() if knowledge_index else 0,
                "context_associations_count": context_integration.store.count() if context_integration else 0,
                "adapters_registered": adapter_fw.registry.count() if adapter_fw else 0,
                "document_pipeline": DocumentComprehensionPipeline.build_snapshot(self._registry),
            },
        )

    def get_document_pipeline_snapshot(self) -> list[dict[str, Any]]:
        return DocumentComprehensionPipeline.build_snapshot(self._registry)

    def snapshot(self) -> dict[str, Any]:
        adapter_fw = self.adapter_framework
        validation = self.validation_framework
        recognition = self.recognition_engine
        extraction = self.extraction_engine
        canonical = self.canonical_engine
        internal_model = self.internal_model_builder
        knowledge_index = self.knowledge_index
        context_integration = self.context_integration_engine
        return {
            "module_name": self.MODULE_NAME,
            "initialized": self._initialized,
            "integration": self._integration.snapshot(),
            "components": self._registry.snapshot(),
            "document_coordinator": (
                self._document_coordinator.snapshot()
                if self._document_coordinator is not None
                else None
            ),
            "validation_framework": validation.snapshot() if validation is not None else None,
            "recognition_engine": recognition.snapshot() if recognition is not None else None,
            "extraction_engine": extraction.snapshot() if extraction is not None else None,
            "canonical_engine": canonical.snapshot() if canonical is not None else None,
            "internal_model_builder": internal_model.snapshot() if internal_model is not None else None,
            "knowledge_index": knowledge_index.snapshot() if knowledge_index is not None else None,
            "context_integration": context_integration.snapshot() if context_integration is not None else None,
            "adapter_framework": adapter_fw.snapshot() if adapter_fw is not None else None,
            "document_pipeline": self.get_document_pipeline_snapshot(),
        }
