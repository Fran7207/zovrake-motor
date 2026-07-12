"""Explanation Generation Engine — integración con el módulo de razonamiento inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.explanation_generation_engine.engine import (
    ExplanationGenerationBuilderEngine,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.integration import (
    ExplanationGenerationMotorIntegration,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationRequest,
    ExplanationGenerationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ExplanationGenerationEngine(IntelligentAnalysisComponentPort):
    """
    Gestor del Explanation Generation Engine (EGE).

    Responsabilidad única: generar explicaciones estructuradas y trazables
    sin modificar datos ni emitir conclusiones.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ExplanationGenerationBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ExplanationGenerationBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "explanation_generation_engine"

    @property
    def component_label(self) -> str:
        return "Explanation Generation Engine"

    @property
    def engine(self) -> ExplanationGenerationBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def generate(
        self,
        request: ExplanationGenerationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ExplanationGenerationResult:
        document_id = str(request.definitive_catalog.get("document_id", ""))
        model_id = str(request.definitive_catalog.get("model_id", ""))
        context_catalog_id = str(getattr(request.context_catalog, "catalog_id", ""))

        if integration is not None and record_traceability:
            bridge = ExplanationGenerationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.begin_explanation_generation(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                context_catalog_id=context_catalog_id,
            )

        result = self._engine.generate(request)

        if integration is not None and record_traceability:
            bridge = ExplanationGenerationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.complete_explanation_generation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
