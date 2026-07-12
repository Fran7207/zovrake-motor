"""Reasoning Result Builder — integración con el módulo de razonamiento inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.reasoning_result_builder.engine import ReasoningResultBuilderEngine
from zovrake_motor.intelligent_analysis.reasoning_result_builder.integration import (
    ReasoningResultMotorIntegration,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    ReasoningResultBuildRequest,
    ReasoningResultBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ReasoningResultBuilder(IntelligentAnalysisComponentPort):
    """
    Gestor del Reasoning Result Builder (RRB).

    Responsabilidad única: construir el Resultado del Análisis Inteligente
    sin modificar información de origen.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ReasoningResultBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ReasoningResultBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "reasoning_result_builder"

    @property
    def component_label(self) -> str:
        return "Reasoning Result Builder"

    @property
    def engine(self) -> ReasoningResultBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: ReasoningResultBuildRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ReasoningResultBuildResult:
        document_id = str(request.definitive_catalog.get("document_id", ""))
        model_id = str(request.definitive_catalog.get("model_id", ""))
        recommendation_catalog_id = str(getattr(request.recommendation_catalog, "catalog_id", ""))

        if integration is not None and record_traceability:
            bridge = ReasoningResultMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.begin_reasoning_result_build(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                recommendation_catalog_id=recommendation_catalog_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = ReasoningResultMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.complete_reasoning_result_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
