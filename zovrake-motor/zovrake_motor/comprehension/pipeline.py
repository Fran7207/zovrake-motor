"""Pipeline documental interno del Módulo de Comprensión."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.document_index import DocumentIndex
from zovrake_motor.comprehension.components.context_manager import DocumentContextManager
from zovrake_motor.comprehension.components.model_builder import InternalModelBuilder
from zovrake_motor.comprehension.components.normalizer import ContentNormalizer
from zovrake_motor.comprehension.components.extractors import ExtractorsRegistry
from zovrake_motor.comprehension.components.validator import DocumentValidator
from zovrake_motor.comprehension.components.format_identifier import FormatIdentifier
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest, DocumentIndexResult
from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest, ContextIntegrationResult
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest, InternalModelBuildResult
from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationRequest, CanonicalRepresentationResult
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ContentExtractionResult
from zovrake_motor.comprehension.registry import ComponentRegistry
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, DocumentRecognitionResult
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, DocumentValidationResult

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration


@dataclass(frozen=True)
class ComprehensionPipelineStage:
    """Etapa del flujo documental interno — referencia arquitectónica."""

    phase: ComprehensionPhase
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


class DocumentComprehensionPipeline:
    """
    Pipeline documental del módulo de Comprensión.

    La validación documental es obligatoria antes de cualquier etapa posterior.
    """

    DEFAULT_STAGES: tuple[ComprehensionPipelineStage, ...] = (
        ComprehensionPipelineStage(ComprehensionPhase.PREPARACION, "Preparación", 1),
        ComprehensionPipelineStage(
            ComprehensionPhase.VALIDACION,
            "Validación Documental",
            2,
            "document_validator",
        ),
        ComprehensionPipelineStage(
            ComprehensionPhase.ADAPTACION,
            "Adaptación Documental",
            3,
            "document_adapters",
        ),
        ComprehensionPipelineStage(
            ComprehensionPhase.IDENTIFICACION,
            "Identificación de Formato",
            4,
            "format_identifier",
        ),
        ComprehensionPipelineStage(
            ComprehensionPhase.EXTRACCION,
            "Extracción",
            5,
            "extractors",
        ),
        ComprehensionPipelineStage(
            ComprehensionPhase.NORMALIZACION,
            "Normalización",
            6,
            "normalizer",
        ),
        ComprehensionPipelineStage(
            ComprehensionPhase.MODELADO,
            "Modelado Interno",
            7,
            "internal_model_builder",
        ),
        ComprehensionPipelineStage(
            ComprehensionPhase.INDEXACION,
            "Indexación",
            8,
            "document_index",
        ),
        ComprehensionPipelineStage(
            ComprehensionPhase.INTEGRACION_CONTEXTO,
            "Integración de Contexto",
            9,
            "context_manager",
        ),
        ComprehensionPipelineStage(ComprehensionPhase.FINALIZACION, "Finalización", 10),
    )

    VALIDATION_STAGE = DEFAULT_STAGES[1]
    RECOGNITION_STAGE = DEFAULT_STAGES[3]
    EXTRACTION_STAGE = DEFAULT_STAGES[4]
    CANONICAL_STAGE = DEFAULT_STAGES[5]
    INTERNAL_MODEL_STAGE = DEFAULT_STAGES[6]
    INDEX_STAGE = DEFAULT_STAGES[7]
    CONTEXT_INTEGRATION_STAGE = DEFAULT_STAGES[8]

    @classmethod
    def ordered_phases(cls) -> tuple[ComprehensionPhase, ...]:
        return tuple(stage.phase for stage in cls.DEFAULT_STAGES)

    @classmethod
    def validation_phase(cls) -> ComprehensionPhase:
        return cls.VALIDATION_STAGE.phase

    @classmethod
    def recognition_phase(cls) -> ComprehensionPhase:
        return cls.RECOGNITION_STAGE.phase

    @classmethod
    def extraction_phase(cls) -> ComprehensionPhase:
        return cls.EXTRACTION_STAGE.phase

    @classmethod
    def canonical_phase(cls) -> ComprehensionPhase:
        return cls.CANONICAL_STAGE.phase

    @classmethod
    def internal_model_phase(cls) -> ComprehensionPhase:
        return cls.INTERNAL_MODEL_STAGE.phase

    @classmethod
    def index_phase(cls) -> ComprehensionPhase:
        return cls.INDEX_STAGE.phase

    @classmethod
    def context_integration_phase(cls) -> ComprehensionPhase:
        return cls.CONTEXT_INTEGRATION_STAGE.phase

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
    def execute_validation(
        cls,
        registry: ComponentRegistry,
        request: DocumentValidationRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
    ) -> DocumentValidationResult:
        """Ejecuta la etapa oficial de validación documental del Pipeline."""
        component = registry.get(cls.VALIDATION_STAGE.component_name or "")
        if not isinstance(component, DocumentValidator):
            raise RuntimeError("Etapa de validación no disponible en el Pipeline documental")
        if not component.is_ready():
            raise RuntimeError("Document Validation Framework no está preparado")
        return component.validate(request, integration=integration)

    @classmethod
    def execute_recognition(
        cls,
        registry: ComponentRegistry,
        request: DocumentRecognitionRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        adapter_framework: Any | None = None,
    ) -> DocumentRecognitionResult:
        """Ejecuta la etapa oficial de reconocimiento documental del Pipeline."""
        component = registry.get(cls.RECOGNITION_STAGE.component_name or "")
        if not isinstance(component, FormatIdentifier):
            raise RuntimeError("Etapa de reconocimiento no disponible en el Pipeline documental")
        if not component.is_ready():
            raise RuntimeError("Document Recognition Engine no está preparado")
        return component.recognize(
            request,
            integration=integration,
            adapter_framework=adapter_framework,
        )

    @classmethod
    def execute_extraction(
        cls,
        registry: ComponentRegistry,
        request: ContentExtractionRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
    ) -> ContentExtractionResult:
        """Ejecuta la etapa oficial de extracción documental del Pipeline."""
        component = registry.get(cls.EXTRACTION_STAGE.component_name or "")
        if not isinstance(component, ExtractorsRegistry):
            raise RuntimeError("Etapa de extracción no disponible en el Pipeline documental")
        if not component.is_ready():
            raise RuntimeError("Content Extraction Engine no está preparado")
        return component.extract(request, integration=integration)

    @classmethod
    def execute_canonical_representation(
        cls,
        registry: ComponentRegistry,
        request: CanonicalRepresentationRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
    ) -> CanonicalRepresentationResult:
        """Ejecuta la etapa oficial de representación canónica del Pipeline."""
        component = registry.get(cls.CANONICAL_STAGE.component_name or "")
        if not isinstance(component, ContentNormalizer):
            raise RuntimeError("Etapa de representación canónica no disponible en el Pipeline documental")
        if not component.is_ready():
            raise RuntimeError("Canonical Representation Engine no está preparado")
        return component.represent(request, integration=integration)

    @classmethod
    def execute_internal_model_build(
        cls,
        registry: ComponentRegistry,
        request: InternalModelBuildRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
    ) -> InternalModelBuildResult:
        """Ejecuta la etapa oficial de modelado interno del Pipeline."""
        component = registry.get(cls.INTERNAL_MODEL_STAGE.component_name or "")
        if not isinstance(component, InternalModelBuilder):
            raise RuntimeError("Etapa de modelado interno no disponible en el Pipeline documental")
        if not component.is_ready():
            raise RuntimeError("Internal Document Model Builder no está preparado")
        return component.build(request, integration=integration)

    @classmethod
    def execute_indexing(
        cls,
        registry: ComponentRegistry,
        request: DocumentIndexRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
    ) -> DocumentIndexResult:
        """Ejecuta la etapa oficial de indexación documental del Pipeline."""
        component = registry.get(cls.INDEX_STAGE.component_name or "")
        if not isinstance(component, DocumentIndex):
            raise RuntimeError("Etapa de indexación no disponible en el Pipeline documental")
        if not component.is_ready():
            raise RuntimeError("Document Knowledge Index no está preparado")
        return component.register(request, integration=integration)

    @classmethod
    def execute_context_integration(
        cls,
        registry: ComponentRegistry,
        request: ContextIntegrationRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
    ) -> ContextIntegrationResult:
        """Ejecuta la etapa oficial de integración de contexto del Pipeline."""
        component = registry.get(cls.CONTEXT_INTEGRATION_STAGE.component_name or "")
        if not isinstance(component, DocumentContextManager):
            raise RuntimeError("Etapa de integración de contexto no disponible en el Pipeline documental")
        if not component.is_ready():
            raise RuntimeError("Context Integration Engine no está preparado")
        return component.integrate(request, integration=integration)
