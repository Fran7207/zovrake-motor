"""Evidence Analysis Engine — integración con el módulo de razonamiento inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.engine import (
    EvidenceAnalysisBuilderEngine,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.integration import (
    EvidenceAnalysisMotorIntegration,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisRequest,
    EvidenceAnalysisResult,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class EvidenceAnalysisEngine(IntelligentAnalysisComponentPort):
    """
    Gestor del Evidence Analysis Engine (EAE).

    Responsabilidad única: identificar y organizar evidencias del
    Modelo Comparativo Definitivo sin interpretar ni modificar datos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: EvidenceAnalysisBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or EvidenceAnalysisBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "evidence_analysis_engine"

    @property
    def component_label(self) -> str:
        return "Evidence Analysis Engine"

    @property
    def engine(self) -> EvidenceAnalysisBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def analyze(
        self,
        request: EvidenceAnalysisRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> EvidenceAnalysisResult:
        catalog_id = str(request.definitive_catalog.get("catalog_id", ""))
        document_id = str(request.definitive_catalog.get("document_id", ""))
        model_id = str(request.definitive_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = EvidenceAnalysisMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.begin_evidence_analysis(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                definitive_catalog_id=catalog_id,
            )

        result = self._engine.analyze(request)

        if integration is not None and record_traceability:
            bridge = EvidenceAnalysisMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.complete_evidence_analysis(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
