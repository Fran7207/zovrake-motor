"""Concept Analysis Engine (CAE) — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.concept_analysis.engine import ConceptAnalysisEngine
from zovrake_motor.classification.concept_analysis.integration import ConceptAnalysisMotorIntegration
from zovrake_motor.classification.concept_analysis.models import ConceptAnalysisRequest, ConceptAnalysisResult

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ConceptAnalysisEngineComponent(ClassificationComponentPort):
    """
    Gestor del Concept Analysis Engine (CAE).

    Responsabilidad única: identificar conceptos candidatos del Modelo Documental Interno.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ConceptAnalysisEngine | None = None,
    ) -> None:
        self._engine = engine or ConceptAnalysisEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "concept_analysis_engine"

    @property
    def component_label(self) -> str:
        return "Concept Analysis Engine"

    @property
    def engine(self) -> ConceptAnalysisEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def analyze(
        self,
        request: ConceptAnalysisRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ConceptAnalysisResult:
        if integration is not None and record_traceability:
            bridge = ConceptAnalysisMotorIntegration.from_classification_integration(integration)
            model_id = str(request.internal_model.get("model_id", ""))
            document_id = str(request.internal_model.get("document", {}).get("document_id", ""))
            bridge.begin_concept_analysis(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
            )

        result = self._engine.analyze(request)

        if integration is not None and record_traceability:
            bridge = ConceptAnalysisMotorIntegration.from_classification_integration(integration)
            bridge.complete_concept_analysis(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
