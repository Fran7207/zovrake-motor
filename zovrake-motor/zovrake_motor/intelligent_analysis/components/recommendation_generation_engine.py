"""Recommendation Generation Engine — integración con el módulo de razonamiento inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.engine import (
    RecommendationGenerationBuilderEngine,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.integration import (
    RecommendationGenerationMotorIntegration,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationRequest,
    RecommendationGenerationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class RecommendationGenerationEngine(IntelligentAnalysisComponentPort):
    """
    Gestor del Recommendation Generation Engine (RGE).

    Responsabilidad única: generar recomendaciones fundamentadas como apoyo
    a la decisión sin sustituir el criterio humano.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: RecommendationGenerationBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or RecommendationGenerationBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "recommendation_generation_engine"

    @property
    def component_label(self) -> str:
        return "Recommendation Generation Engine"

    @property
    def engine(self) -> RecommendationGenerationBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def generate(
        self,
        request: RecommendationGenerationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> RecommendationGenerationResult:
        document_id = str(request.definitive_catalog.get("document_id", ""))
        model_id = str(request.definitive_catalog.get("model_id", ""))
        explanation_catalog_id = str(getattr(request.explanation_catalog, "catalog_id", ""))

        if integration is not None and record_traceability:
            bridge = RecommendationGenerationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.begin_recommendation_generation(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                explanation_catalog_id=explanation_catalog_id,
            )

        result = self._engine.generate(request)

        if integration is not None and record_traceability:
            bridge = RecommendationGenerationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.complete_recommendation_generation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
