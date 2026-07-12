"""Motor central del Consistency Evaluation Engine (CEE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.catalog_store import (
    ConsistencyEvaluationCatalogStore,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.executor import (
    ConsistencyEvaluationExecutor,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceAnalysisCatalogGateway,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.integration_hooks import (
    RiskAnalysisEngineIntegrationPoint,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationRequest,
    ConsistencyEvaluationResult,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.port import (
    ConsistencyEvaluatorPort,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.registry import (
    ConsistencyEvaluatorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ConsistencyEvaluationEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ConsistencyEvaluationBuilderEngine:
    """
    Consistency Evaluation Engine (CEE).

    Evalúa la consistencia lógica y estructural de evidencias organizadas por el EAE.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_EVALUATOR_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ConsistencyEvaluatorRegistry | None = None,
        gateway: EvidenceAnalysisCatalogGateway | None = None,
        catalog_store: ConsistencyEvaluationCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ConsistencyEvaluatorRegistry()
        self._gateway = gateway or EvidenceAnalysisCatalogGateway()
        self._catalog_store = catalog_store or ConsistencyEvaluationCatalogStore()
        self._executor: ConsistencyEvaluationExecutor | None = None
        self._rae_hook: RiskAnalysisEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ConsistencyEvaluatorRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ConsistencyEvaluationCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ConsistencyEvaluationExecutor:
        if self._executor is None:
            self._executor = ConsistencyEvaluationExecutor(self._registry)
        return self._executor

    @property
    def risk_analysis_integration(self) -> RiskAnalysisEngineIntegrationPoint:
        if self._rae_hook is None:
            self._rae_hook = RiskAnalysisEngineIntegrationPoint(
                settings=self._consistency_evaluation_settings(),
            )
        return self._rae_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_EVALUATOR_COUNT

    def initialize(self) -> None:
        settings = self._consistency_evaluation_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ConsistencyEvaluationExecutor(self._registry)
        self._rae_hook = RiskAnalysisEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def evaluate(self, request: ConsistencyEvaluationRequest) -> ConsistencyEvaluationResult:
        settings = self._consistency_evaluation_settings()
        catalog_view = self._gateway.validate(request.evidence_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        rae_status = self.risk_analysis_integration.prepare_for_future_risk_analysis(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"risk_analysis_engine_status={rae_status['status']}",
        )
        return ConsistencyEvaluationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            inconsistencies_count=result.inconsistencies_count,
            sufficient_profiles_count=result.sufficient_profiles_count,
            insufficient_profiles_count=result.insufficient_profiles_count,
            evidence_catalog_preserved=result.evidence_catalog_preserved,
            source_data_preserved=result.source_data_preserved,
            evaluators_executed=result.evaluators_executed,
            incidents=result.incidents,
            technical_observations=observations,
        )

    def extend(self, evaluator: ConsistencyEvaluatorPort) -> None:
        """Incorpora un nuevo evaluador mediante extensión sin modificar el núcleo."""
        self._registry.register(evaluator)

    def _consistency_evaluation_settings(self) -> ConsistencyEvaluationEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.intelligent_analysis().consistency_evaluation_engine
        return ConsistencyEvaluationEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._consistency_evaluation_settings()
        return {
            "initialized": self._initialized,
            "evaluators_count": self._registry.count(),
            "evaluators": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "risk_analysis_integration": self.risk_analysis_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "organized_evidence_evaluator_enabled": (
                    settings.organized_evidence_evaluator_enabled
                ),
                "detect_commercial_technical_contradictions": (
                    settings.detect_commercial_technical_contradictions
                ),
                "detect_provider_attribute_differences": (
                    settings.detect_provider_attribute_differences
                ),
                "detect_integrity_violations": settings.detect_integrity_violations,
                "detect_incomplete_references": settings.detect_incomplete_references,
                "detect_contradictions": settings.detect_contradictions,
                "inconsistency_id_prefix": settings.inconsistency_id_prefix,
                "risk_analysis_engine_prepared": settings.risk_analysis_engine_prepared,
            },
        }
