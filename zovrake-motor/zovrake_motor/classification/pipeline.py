"""Pipeline interno del Módulo de Clasificación Inteligente."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.registry import ComponentRegistry

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration


@dataclass(frozen=True)
class ClassificationPipelineStage:
    """Etapa del flujo de clasificación interno — referencia arquitectónica."""

    phase: ClassificationPhase
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


class ClassificationPipeline:
    """
    Pipeline de clasificación del módulo.

    El análisis de conceptos es la primera etapa funcional del flujo.
    """

    DEFAULT_STAGES: tuple[ClassificationPipelineStage, ...] = (
        ClassificationPipelineStage(ClassificationPhase.PREPARACION, "Preparación", 1),
        ClassificationPipelineStage(
            ClassificationPhase.ANALISIS_CONCEPTOS,
            "Análisis de Conceptos",
            2,
            "concept_analysis_engine",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.CLASIFICACION_MATERIALES,
            "Clasificación de Materiales",
            3,
            "material_classification_engine",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.CLASIFICACION_SERVICIOS,
            "Clasificación de Servicios",
            4,
            "service_classification_engine",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.NORMALIZACION_CONCEPTOS,
            "Normalización Conceptual",
            5,
            "concept_normalization_engine",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.DETECCION_EQUIVALENCIAS,
            "Detección de Equivalencias",
            6,
            "equivalence_detection_engine",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.CONSTRUCCION_GRUPOS,
            "Construcción de Grupos Comparables",
            7,
            "comparable_group_builder",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.IDENTIFICACION_GRUPOS,
            "Identificación de Grupos",
            8,
            "group_identifier_generator",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.ASOCIACION_CONTEXTO,
            "Asociación de Contexto",
            9,
            "context_association_engine",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.TRAZABILIDAD,
            "Trazabilidad",
            10,
            "traceability_manager",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.EVALUACION_CONFIANZA,
            "Evaluación de Confianza",
            11,
            "confidence_evaluation_engine",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.MODELO_DOMINIO,
            "Modelo de Dominio Comparativo",
            12,
            "comparative_domain_model_builder",
        ),
        ClassificationPipelineStage(
            ClassificationPhase.VALIDACION_CALIDAD,
            "Validación de Calidad",
            13,
            "classification_quality_framework",
        ),
        ClassificationPipelineStage(ClassificationPhase.FINALIZACION, "Finalización", 14),
    )

    CONCEPT_ANALYSIS_STAGE = DEFAULT_STAGES[1]
    MATERIAL_CLASSIFICATION_STAGE = DEFAULT_STAGES[2]
    SERVICE_CLASSIFICATION_STAGE = DEFAULT_STAGES[3]
    CONCEPT_NORMALIZATION_STAGE = DEFAULT_STAGES[4]
    EQUIVALENCE_DETECTION_STAGE = DEFAULT_STAGES[5]
    COMPARABLE_GROUP_BUILD_STAGE = DEFAULT_STAGES[6]
    CONTEXT_ASSOCIATION_STAGE = DEFAULT_STAGES[8]
    COMPARATIVE_DOMAIN_MODEL_STAGE = DEFAULT_STAGES[11]
    QUALITY_VALIDATION_STAGE = DEFAULT_STAGES[12]

    @classmethod
    def ordered_phases(cls) -> tuple[ClassificationPhase, ...]:
        return tuple(stage.phase for stage in cls.DEFAULT_STAGES)

    @classmethod
    def concept_analysis_phase(cls) -> ClassificationPhase:
        return cls.CONCEPT_ANALYSIS_STAGE.phase

    @classmethod
    def material_classification_phase(cls) -> ClassificationPhase:
        return cls.MATERIAL_CLASSIFICATION_STAGE.phase

    @classmethod
    def service_classification_phase(cls) -> ClassificationPhase:
        return cls.SERVICE_CLASSIFICATION_STAGE.phase

    @classmethod
    def concept_normalization_phase(cls) -> ClassificationPhase:
        return cls.CONCEPT_NORMALIZATION_STAGE.phase

    @classmethod
    def equivalence_detection_phase(cls) -> ClassificationPhase:
        return cls.EQUIVALENCE_DETECTION_STAGE.phase

    @classmethod
    def comparable_group_build_phase(cls) -> ClassificationPhase:
        return cls.COMPARABLE_GROUP_BUILD_STAGE.phase

    @classmethod
    def context_association_phase(cls) -> ClassificationPhase:
        return cls.CONTEXT_ASSOCIATION_STAGE.phase

    @classmethod
    def comparative_domain_model_phase(cls) -> ClassificationPhase:
        return cls.COMPARATIVE_DOMAIN_MODEL_STAGE.phase

    @classmethod
    def quality_validation_phase(cls) -> ClassificationPhase:
        return cls.QUALITY_VALIDATION_STAGE.phase

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
    def execute_concept_analysis(
        cls,
        registry: ComponentRegistry,
        request: ConceptAnalysisRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> ConceptAnalysisResult:
        """Ejecuta la etapa oficial de análisis de conceptos del Pipeline."""
        component = registry.get(cls.CONCEPT_ANALYSIS_STAGE.component_name or "")
        if not isinstance(component, ConceptAnalysisEngineComponent):
            raise RuntimeError("Etapa de análisis de conceptos no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Concept Analysis Engine no está preparado")
        return component.analyze(request, integration=integration)

    @classmethod
    def execute_material_classification(
        cls,
        registry: ComponentRegistry,
        request: MaterialClassificationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> MaterialClassificationResult:
        """Ejecuta la etapa oficial de clasificación de materiales del Pipeline."""
        component = registry.get(cls.MATERIAL_CLASSIFICATION_STAGE.component_name or "")
        if not isinstance(component, MaterialClassificationEngineComponent):
            raise RuntimeError("Etapa de clasificación de materiales no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Material Classification Engine no está preparado")
        return component.classify(request, integration=integration)

    @classmethod
    def execute_service_classification(
        cls,
        registry: ComponentRegistry,
        request: ServiceClassificationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> ServiceClassificationResult:
        """Ejecuta la etapa oficial de clasificación de servicios del Pipeline."""
        component = registry.get(cls.SERVICE_CLASSIFICATION_STAGE.component_name or "")
        if not isinstance(component, ServiceClassificationEngineComponent):
            raise RuntimeError("Etapa de clasificación de servicios no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Service Classification Engine no está preparado")
        return component.classify(request, integration=integration)

    @classmethod
    def execute_concept_normalization(
        cls,
        registry: ComponentRegistry,
        request: ConceptNormalizationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> ConceptNormalizationResult:
        """Ejecuta la etapa oficial de normalización conceptual del Pipeline."""
        component = registry.get(cls.CONCEPT_NORMALIZATION_STAGE.component_name or "")
        if not isinstance(component, ConceptNormalizationEngineComponent):
            raise RuntimeError("Etapa de normalización conceptual no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Concept Normalization Engine no está preparado")
        return component.normalize(request, integration=integration)

    @classmethod
    def execute_equivalence_detection(
        cls,
        registry: ComponentRegistry,
        request: EquivalenceDetectionRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> EquivalenceDetectionResult:
        """Ejecuta la etapa oficial de detección de equivalencias del Pipeline."""
        component = registry.get(cls.EQUIVALENCE_DETECTION_STAGE.component_name or "")
        if not isinstance(component, EquivalenceDetectionEngineComponent):
            raise RuntimeError("Etapa de detección de equivalencias no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Equivalence Detection Engine no está preparado")
        return component.detect(request, integration=integration)

    @classmethod
    def execute_comparable_group_build(
        cls,
        registry: ComponentRegistry,
        request: ComparableGroupBuildRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> ComparableGroupBuildResult:
        """Ejecuta la etapa oficial de construcción de grupos comparables del Pipeline."""
        component = registry.get(cls.COMPARABLE_GROUP_BUILD_STAGE.component_name or "")
        if not isinstance(component, ComparableGroupBuilder):
            raise RuntimeError("Etapa de construcción de grupos comparables no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Comparable Group Builder no está preparado")
        return component.build(request, integration=integration)

    @classmethod
    def execute_context_association(
        cls,
        registry: ComponentRegistry,
        request: ContextAssociationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> ContextAssociationResult:
        """Ejecuta la etapa oficial de asociación de contexto del Pipeline."""
        component = registry.get(cls.CONTEXT_ASSOCIATION_STAGE.component_name or "")
        if not isinstance(component, ContextAssociationEngineComponent):
            raise RuntimeError("Etapa de asociación de contexto no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Context Association Engine no está preparado")
        return component.associate(request, integration=integration)

    @classmethod
    def execute_comparative_domain_model_build(
        cls,
        registry: ComponentRegistry,
        request: ComparativeDomainModelBuildRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> ComparativeDomainModelBuildResult:
        """Ejecuta la etapa oficial de construcción del modelo comparativo del Pipeline."""
        component = registry.get(cls.COMPARATIVE_DOMAIN_MODEL_STAGE.component_name or "")
        if not isinstance(component, ComparativeDomainModelBuilder):
            raise RuntimeError("Etapa de modelo de dominio comparativo no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Comparative Domain Model Builder no está preparado")
        return component.build(request, integration=integration)

    @classmethod
    def execute_quality_validation(
        cls,
        registry: ComponentRegistry,
        request: ClassificationQualityValidationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
    ) -> ClassificationQualityValidationResult:
        """Ejecuta la etapa oficial de validación de calidad del Pipeline."""
        component = registry.get(cls.QUALITY_VALIDATION_STAGE.component_name or "")
        if not isinstance(component, ClassificationQualityFramework):
            raise RuntimeError("Etapa de validación de calidad no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Classification Quality Framework no está preparado")
        return component.validate(request, integration=integration)
