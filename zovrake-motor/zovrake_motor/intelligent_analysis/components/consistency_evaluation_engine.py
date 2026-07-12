"""Consistency Evaluation Engine — integración con el módulo de razonamiento inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.engine import (
    ConsistencyEvaluationBuilderEngine,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.integration import (
    ConsistencyEvaluationMotorIntegration,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationRequest,
    ConsistencyEvaluationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ConsistencyEvaluationEngine(IntelligentAnalysisComponentPort):
    """
    Gestor del Consistency Evaluation Engine (CEE).

    Responsabilidad única: evaluar la consistencia de evidencias organizadas
    por el EAE sin interpretar ni modificar datos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ConsistencyEvaluationBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ConsistencyEvaluationBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "consistency_evaluation_engine"

    @property
    def component_label(self) -> str:
        return "Consistency Evaluation Engine"

    @property
    def engine(self) -> ConsistencyEvaluationBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def evaluate(
        self,
        request: ConsistencyEvaluationRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ConsistencyEvaluationResult:
        catalog = request.evidence_catalog
        document_id = str(getattr(catalog, "document_id", ""))
        model_id = str(getattr(catalog, "model_id", ""))
        catalog_id = str(getattr(catalog, "catalog_id", ""))

        if integration is not None and record_traceability:
            bridge = ConsistencyEvaluationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.begin_consistency_evaluation(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                evidence_catalog_id=catalog_id,
            )

        result = self._engine.evaluate(request)

        if integration is not None and record_traceability:
            bridge = ConsistencyEvaluationMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.complete_consistency_evaluation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
