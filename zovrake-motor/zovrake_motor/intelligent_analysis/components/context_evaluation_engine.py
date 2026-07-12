"""Context Evaluation Engine — integración con el módulo de razonamiento inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.context_evaluation_engine.engine import (
    ContextEvaluationBuilderEngine,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.integration import (
    ContextEvaluationMotorIntegration,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationRequest,
    ContextEvaluationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ContextEvaluationEngine(IntelligentAnalysisComponentPort):
    """
    Gestor del Context Evaluation Engine (CxEE).

    Responsabilidad única: evaluar la relación entre contexto del requerimiento
    y evidencias sin modificar datos ni emitir conclusiones.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ContextEvaluationBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ContextEvaluationBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "context_evaluation_engine"

    @property
    def component_label(self) -> str:
        return "Context Evaluation Engine"

    @property
    def engine(self) -> ContextEvaluationBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def evaluate(
        self,
        request: ContextEvaluationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ContextEvaluationResult:
        document_id = str(request.definitive_catalog.get("document_id", ""))
        model_id = str(request.definitive_catalog.get("model_id", ""))
        evidence_catalog_id = str(getattr(request.evidence_catalog, "catalog_id", ""))
        risk_catalog_id = str(getattr(request.risk_catalog, "catalog_id", ""))

        if integration is not None and record_traceability:
            bridge = ContextEvaluationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.begin_context_evaluation(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                evidence_catalog_id=evidence_catalog_id,
                risk_catalog_id=risk_catalog_id,
            )

        result = self._engine.evaluate(request)

        if integration is not None and record_traceability:
            bridge = ContextEvaluationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.complete_context_evaluation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
