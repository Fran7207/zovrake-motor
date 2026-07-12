"""Pipeline interno del Módulo de Razonamiento y Resultado del Análisis Inteligente."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisRequest,
    EvidenceAnalysisResult,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationRequest,
    ConsistencyEvaluationResult,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    RiskAnalysisRequest,
    RiskAnalysisResult,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationRequest,
    ContextEvaluationResult,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationRequest,
    ExplanationGenerationResult,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationRequest,
    RecommendationGenerationResult,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    ReasoningResultBuildRequest,
    ReasoningResultBuildResult,
)
from zovrake_motor.intelligent_analysis.components.evidence_analysis_engine import (
    EvidenceAnalysisEngine,
)
from zovrake_motor.intelligent_analysis.components.consistency_evaluation_engine import (
    ConsistencyEvaluationEngine,
)
from zovrake_motor.intelligent_analysis.components.risk_analysis_engine import RiskAnalysisEngine
from zovrake_motor.intelligent_analysis.components.context_evaluation_engine import (
    ContextEvaluationEngine,
)
from zovrake_motor.intelligent_analysis.components.explanation_generation_engine import (
    ExplanationGenerationEngine,
)
from zovrake_motor.intelligent_analysis.components.recommendation_generation_engine import (
    RecommendationGenerationEngine,
)
from zovrake_motor.intelligent_analysis.components.reasoning_result_builder import (
    ReasoningResultBuilder,
)
from zovrake_motor.intelligent_analysis.registry import ComponentRegistry

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration


@dataclass(frozen=True)
class IntelligentAnalysisPipelineStage:
    """Etapa del flujo de razonamiento interno — referencia arquitectónica."""

    phase: IntelligentAnalysisPhase
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


class IntelligentAnalysisPipeline:
    """
    Pipeline de razonamiento inteligente del módulo.

    El consumo del Modelo Comparativo Definitivo es la primera etapa funcional
    preparada del flujo.
    """

    DEFAULT_STAGES: tuple[IntelligentAnalysisPipelineStage, ...] = (
        IntelligentAnalysisPipelineStage(IntelligentAnalysisPhase.PREPARACION, "Preparación", 1),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.CONSUMO_MODELO_COMPARATIVO_DEFINITIVO,
            "Consumo del Modelo Comparativo Definitivo",
            2,
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS,
            "Análisis de Evidencias",
            3,
            "evidence_analysis_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.EVALUACION_CONSISTENCIA,
            "Evaluación de Consistencia",
            4,
            "consistency_evaluation_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.ANALISIS_RIESGOS,
            "Análisis de Riesgos",
            5,
            "risk_analysis_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.EVALUACION_CONTEXTO,
            "Evaluación de Contexto",
            6,
            "context_evaluation_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.GENERACION_EXPLICACIONES,
            "Generación de Explicaciones",
            7,
            "explanation_generation_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.GENERACION_CONCLUSIONES,
            "Generación de Conclusiones",
            8,
            "conclusion_generation_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.GENERACION_RECOMENDACIONES,
            "Generación de Recomendaciones",
            9,
            "recommendation_generation_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE,
            "Construcción del Resultado del Análisis Inteligente",
            10,
            "reasoning_result_builder",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.GESTION_CONFIANZA,
            "Gestión de Confianza",
            11,
            "confidence_management_engine",
        ),
        IntelligentAnalysisPipelineStage(
            IntelligentAnalysisPhase.GESTION_TRAZABILIDAD,
            "Gestión de Trazabilidad",
            12,
            "traceability_management_engine",
        ),
        IntelligentAnalysisPipelineStage(IntelligentAnalysisPhase.FINALIZACION, "Finalización", 13),
    )

    DEFINITIVE_MODEL_CONSUMPTION_STAGE = DEFAULT_STAGES[1]
    EVIDENCE_ANALYSIS_STAGE = DEFAULT_STAGES[2]
    CONSISTENCY_EVALUATION_STAGE = DEFAULT_STAGES[3]
    RISK_ANALYSIS_STAGE = DEFAULT_STAGES[4]
    CONTEXT_EVALUATION_STAGE = DEFAULT_STAGES[5]
    EXPLANATION_GENERATION_STAGE = DEFAULT_STAGES[6]
    CONCLUSION_GENERATION_STAGE = DEFAULT_STAGES[7]
    RECOMMENDATION_GENERATION_STAGE = DEFAULT_STAGES[8]
    REASONING_RESULT_BUILD_STAGE = DEFAULT_STAGES[9]
    CONFIDENCE_MANAGEMENT_STAGE = DEFAULT_STAGES[10]
    TRACEABILITY_MANAGEMENT_STAGE = DEFAULT_STAGES[11]

    @classmethod
    def ordered_phases(cls) -> tuple[IntelligentAnalysisPhase, ...]:
        return tuple(stage.phase for stage in cls.DEFAULT_STAGES)

    @classmethod
    def definitive_model_consumption_phase(cls) -> IntelligentAnalysisPhase:
        return cls.DEFINITIVE_MODEL_CONSUMPTION_STAGE.phase

    @classmethod
    def evidence_analysis_phase(cls) -> IntelligentAnalysisPhase:
        return cls.EVIDENCE_ANALYSIS_STAGE.phase

    @classmethod
    def consistency_evaluation_phase(cls) -> IntelligentAnalysisPhase:
        return cls.CONSISTENCY_EVALUATION_STAGE.phase

    @classmethod
    def risk_analysis_phase(cls) -> IntelligentAnalysisPhase:
        return cls.RISK_ANALYSIS_STAGE.phase

    @classmethod
    def context_evaluation_phase(cls) -> IntelligentAnalysisPhase:
        return cls.CONTEXT_EVALUATION_STAGE.phase

    @classmethod
    def explanation_generation_phase(cls) -> IntelligentAnalysisPhase:
        return cls.EXPLANATION_GENERATION_STAGE.phase

    @classmethod
    def recommendation_generation_phase(cls) -> IntelligentAnalysisPhase:
        return cls.RECOMMENDATION_GENERATION_STAGE.phase

    @classmethod
    def reasoning_result_build_phase(cls) -> IntelligentAnalysisPhase:
        return cls.REASONING_RESULT_BUILD_STAGE.phase

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
    def execute_evidence_analysis(
        cls,
        registry: ComponentRegistry,
        request: EvidenceAnalysisRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
    ) -> EvidenceAnalysisResult:
        """Ejecuta la primera etapa funcional del PM7 — análisis de evidencias."""
        component = registry.get(cls.EVIDENCE_ANALYSIS_STAGE.component_name or "")
        if not isinstance(component, EvidenceAnalysisEngine):
            raise RuntimeError("Etapa de análisis de evidencias no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Evidence Analysis Engine no está preparado")
        return component.analyze(request, integration=integration)

    @classmethod
    def execute_consistency_evaluation(
        cls,
        registry: ComponentRegistry,
        request: ConsistencyEvaluationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
    ) -> ConsistencyEvaluationResult:
        """Ejecuta la segunda etapa funcional del PM7 — evaluación de consistencia."""
        component = registry.get(cls.CONSISTENCY_EVALUATION_STAGE.component_name or "")
        if not isinstance(component, ConsistencyEvaluationEngine):
            raise RuntimeError("Etapa de evaluación de consistencia no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Consistency Evaluation Engine no está preparado")
        return component.evaluate(request, integration=integration)

    @classmethod
    def execute_risk_analysis(
        cls,
        registry: ComponentRegistry,
        request: RiskAnalysisRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
    ) -> RiskAnalysisResult:
        """Ejecuta la tercera etapa funcional del PM7 — análisis de riesgos."""
        component = registry.get(cls.RISK_ANALYSIS_STAGE.component_name or "")
        if not isinstance(component, RiskAnalysisEngine):
            raise RuntimeError("Etapa de análisis de riesgos no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Risk Analysis Engine no está preparado")
        return component.analyze(request, integration=integration)

    @classmethod
    def execute_context_evaluation(
        cls,
        registry: ComponentRegistry,
        request: ContextEvaluationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
    ) -> ContextEvaluationResult:
        """Ejecuta la cuarta etapa funcional del PM7 — evaluación contextual."""
        component = registry.get(cls.CONTEXT_EVALUATION_STAGE.component_name or "")
        if not isinstance(component, ContextEvaluationEngine):
            raise RuntimeError("Etapa de evaluación contextual no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Context Evaluation Engine no está preparado")
        return component.evaluate(request, integration=integration)

    @classmethod
    def execute_explanation_generation(
        cls,
        registry: ComponentRegistry,
        request: ExplanationGenerationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
    ) -> ExplanationGenerationResult:
        """Ejecuta la quinta etapa funcional del PM7 — generación de explicaciones."""
        component = registry.get(cls.EXPLANATION_GENERATION_STAGE.component_name or "")
        if not isinstance(component, ExplanationGenerationEngine):
            raise RuntimeError("Etapa de generación de explicaciones no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Explanation Generation Engine no está preparado")
        return component.generate(request, integration=integration)

    @classmethod
    def execute_recommendation_generation(
        cls,
        registry: ComponentRegistry,
        request: RecommendationGenerationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
    ) -> RecommendationGenerationResult:
        """Ejecuta la etapa de generación de recomendaciones del PM7."""
        component = registry.get(cls.RECOMMENDATION_GENERATION_STAGE.component_name or "")
        if not isinstance(component, RecommendationGenerationEngine):
            raise RuntimeError("Etapa de generación de recomendaciones no disponible en el Pipeline")
        if not component.is_ready():
            raise RuntimeError("Recommendation Generation Engine no está preparado")
        return component.generate(request, integration=integration)

    @classmethod
    def execute_reasoning_result_build(
        cls,
        registry: ComponentRegistry,
        request: ReasoningResultBuildRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
    ) -> ReasoningResultBuildResult:
        """Ejecuta la construcción del Resultado del Análisis Inteligente del PM7."""
        component = registry.get(cls.REASONING_RESULT_BUILD_STAGE.component_name or "")
        if not isinstance(component, ReasoningResultBuilder):
            raise RuntimeError(
                "Etapa de construcción del Resultado del Análisis Inteligente no disponible",
            )
        if not component.is_ready():
            raise RuntimeError("Reasoning Result Builder no está preparado")
        return component.build(request, integration=integration)
