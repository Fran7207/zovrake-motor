"""Motor central del Risk Analysis Engine (RAE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.risk_analysis_engine.catalog_store import (
    RiskAnalysisCatalogStore,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.executor import RiskAnalysisExecutor
from zovrake_motor.intelligent_analysis.risk_analysis_engine.gateway import (
    EvidenceAndConsistencyInputGateway,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.integration_hooks import (
    ContextEvaluationEngineIntegrationPoint,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    RiskAnalysisRequest,
    RiskAnalysisResult,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.port import RiskAnalyzerPort
from zovrake_motor.intelligent_analysis.risk_analysis_engine.registry import RiskAnalyzerRegistry
from zovrake_motor.config.categories.intelligent_analysis import RiskAnalysisEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class RiskAnalysisBuilderEngine:
    """
    Risk Analysis Engine (RAE).

    Identifica, clasifica y registra riesgos a partir de evidencias y consistencia.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_ANALYZER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: RiskAnalyzerRegistry | None = None,
        gateway: EvidenceAndConsistencyInputGateway | None = None,
        catalog_store: RiskAnalysisCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or RiskAnalyzerRegistry()
        self._gateway = gateway or EvidenceAndConsistencyInputGateway()
        self._catalog_store = catalog_store or RiskAnalysisCatalogStore()
        self._executor: RiskAnalysisExecutor | None = None
        self._cxee_hook: ContextEvaluationEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> RiskAnalyzerRegistry:
        return self._registry

    @property
    def catalog_store(self) -> RiskAnalysisCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> RiskAnalysisExecutor:
        if self._executor is None:
            self._executor = RiskAnalysisExecutor(self._registry)
        return self._executor

    @property
    def context_evaluation_integration(self) -> ContextEvaluationEngineIntegrationPoint:
        if self._cxee_hook is None:
            self._cxee_hook = ContextEvaluationEngineIntegrationPoint(
                settings=self._risk_analysis_settings(),
            )
        return self._cxee_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_ANALYZER_COUNT

    def initialize(self) -> None:
        settings = self._risk_analysis_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = RiskAnalysisExecutor(self._registry)
        self._cxee_hook = ContextEvaluationEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def analyze(self, request: RiskAnalysisRequest) -> RiskAnalysisResult:
        settings = self._risk_analysis_settings()
        input_view = self._gateway.validate(
            evidence_catalog=request.evidence_catalog,
            consistency_catalog=request.consistency_catalog,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        cxee_status = self.context_evaluation_integration.prepare_for_future_context_evaluation(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"context_evaluation_engine_status={cxee_status['status']}",
        )
        return RiskAnalysisResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            risks_count=result.risks_count,
            evidence_catalog_preserved=result.evidence_catalog_preserved,
            consistency_catalog_preserved=result.consistency_catalog_preserved,
            source_data_preserved=result.source_data_preserved,
            analyzers_executed=result.analyzers_executed,
            incidents=result.incidents,
            technical_observations=observations,
        )

    def extend(self, analyzer: RiskAnalyzerPort) -> None:
        """Incorpora un nuevo analizador mediante extensión sin modificar el núcleo."""
        self._registry.register(analyzer)

    def _risk_analysis_settings(self) -> RiskAnalysisEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.intelligent_analysis().risk_analysis_engine
        return RiskAnalysisEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._risk_analysis_settings()
        return {
            "initialized": self._initialized,
            "analyzers_count": self._registry.count(),
            "analyzers": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "context_evaluation_integration": self.context_evaluation_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_input_immutability": settings.preserve_input_immutability,
                "organized_evidence_risk_analyzer_enabled": (
                    settings.organized_evidence_risk_analyzer_enabled
                ),
                "detect_documentation_risks": settings.detect_documentation_risks,
                "detect_consistency_risks": settings.detect_consistency_risks,
                "detect_information_risks": settings.detect_information_risks,
                "detect_commercial_risks": settings.detect_commercial_risks,
                "detect_technical_risks": settings.detect_technical_risks,
                "risk_id_prefix": settings.risk_id_prefix,
                "context_evaluation_engine_prepared": settings.context_evaluation_engine_prepared,
            },
        }
