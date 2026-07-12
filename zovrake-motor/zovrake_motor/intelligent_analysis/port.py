"""Contrato del Módulo de Razonamiento y Resultado del Análisis Inteligente."""

from __future__ import annotations

from abc import ABC, abstractmethod

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
from zovrake_motor.intelligent_analysis.models import (
    IntelligentAnalysisRequest,
    IntelligentAnalysisResult,
)


class IntelligentAnalysisPort(ABC):
    """Punto de entrada del módulo de Razonamiento Inteligente."""

    @abstractmethod
    def prepare(self, request: IntelligentAnalysisRequest) -> IntelligentAnalysisResult:
        """Preparará el razonamiento inteligente — sin procesamiento en esta etapa."""

    @abstractmethod
    def analyze_evidence(
        self,
        request: EvidenceAnalysisRequest,
    ) -> EvidenceAnalysisResult:
        """Analizará evidencias del Modelo Comparativo Definitivo."""

    @abstractmethod
    def evaluate_consistency(
        self,
        request: ConsistencyEvaluationRequest,
    ) -> ConsistencyEvaluationResult:
        """Evaluará la consistencia de evidencias organizadas por el EAE."""

    @abstractmethod
    def analyze_risks(
        self,
        request: RiskAnalysisRequest,
    ) -> RiskAnalysisResult:
        """Analizará riesgos a partir de evidencias y consistencia evaluada."""

    @abstractmethod
    def evaluate_context(
        self,
        request: ContextEvaluationRequest,
    ) -> ContextEvaluationResult:
        """Evaluará la relación entre contexto del requerimiento y evidencias."""

    @abstractmethod
    def generate_explanations(
        self,
        request: ExplanationGenerationRequest,
    ) -> ExplanationGenerationResult:
        """Generará explicaciones estructuradas basadas en evidencias."""

    @abstractmethod
    def generate_recommendations(
        self,
        request: RecommendationGenerationRequest,
    ) -> RecommendationGenerationResult:
        """Generará recomendaciones fundamentadas como apoyo a la decisión."""

    @abstractmethod
    def build_intelligent_analysis_results(
        self,
        request: ReasoningResultBuildRequest,
    ) -> ReasoningResultBuildResult:
        """Construirá el Resultado del Análisis Inteligente por Grupo Comparable."""
