"""Risk Analysis Engine — integración con el módulo de razonamiento inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.risk_analysis_engine.engine import RiskAnalysisBuilderEngine
from zovrake_motor.intelligent_analysis.risk_analysis_engine.integration import (
    RiskAnalysisMotorIntegration,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    RiskAnalysisRequest,
    RiskAnalysisResult,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class RiskAnalysisEngine(IntelligentAnalysisComponentPort):
    """
    Gestor del Risk Analysis Engine (RAE).

    Responsabilidad única: identificar, clasificar y registrar riesgos
    a partir de evidencias y consistencia sin modificar datos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: RiskAnalysisBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or RiskAnalysisBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "risk_analysis_engine"

    @property
    def component_label(self) -> str:
        return "Risk Analysis Engine"

    @property
    def engine(self) -> RiskAnalysisBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def analyze(
        self,
        request: RiskAnalysisRequest,
        *,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> RiskAnalysisResult:
        evidence_catalog = request.evidence_catalog
        consistency_catalog = request.consistency_catalog
        document_id = str(getattr(evidence_catalog, "document_id", ""))
        model_id = str(getattr(evidence_catalog, "model_id", ""))
        evidence_catalog_id = str(getattr(evidence_catalog, "catalog_id", ""))
        consistency_catalog_id = str(getattr(consistency_catalog, "catalog_id", ""))

        if integration is not None and record_traceability:
            bridge = RiskAnalysisMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.begin_risk_analysis(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                evidence_catalog_id=evidence_catalog_id,
                consistency_catalog_id=consistency_catalog_id,
            )

        result = self._engine.analyze(request)

        if integration is not None and record_traceability:
            bridge = RiskAnalysisMotorIntegration.from_intelligent_analysis_integration(
                integration,
            )
            bridge.complete_risk_analysis(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
