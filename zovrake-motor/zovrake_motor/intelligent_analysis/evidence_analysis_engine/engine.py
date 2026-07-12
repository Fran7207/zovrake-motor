"""Motor central del Evidence Analysis Engine (EAE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.catalog_store import (
    EvidenceAnalysisCatalogStore,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.executor import (
    EvidenceAnalysisExecutor,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogGateway,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.integration_hooks import (
    ConsistencyEvaluationEngineIntegrationPoint,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisRequest,
    EvidenceAnalysisResult,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.port import EvidenceAnalyzerPort
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.registry import (
    EvidenceAnalyzerRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import EvidenceAnalysisEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class EvidenceAnalysisBuilderEngine:
    """
    Evidence Analysis Engine (EAE).

    Analiza sistemáticamente las evidencias del Modelo Comparativo Definitivo.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_ANALYZER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: EvidenceAnalyzerRegistry | None = None,
        gateway: DefinitiveComparativeModelCatalogGateway | None = None,
        catalog_store: EvidenceAnalysisCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or EvidenceAnalyzerRegistry()
        self._gateway = gateway or DefinitiveComparativeModelCatalogGateway()
        self._catalog_store = catalog_store or EvidenceAnalysisCatalogStore()
        self._executor: EvidenceAnalysisExecutor | None = None
        self._cee_hook: ConsistencyEvaluationEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> EvidenceAnalyzerRegistry:
        return self._registry

    @property
    def catalog_store(self) -> EvidenceAnalysisCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> EvidenceAnalysisExecutor:
        if self._executor is None:
            self._executor = EvidenceAnalysisExecutor(self._registry)
        return self._executor

    @property
    def consistency_evaluation_integration(self) -> ConsistencyEvaluationEngineIntegrationPoint:
        if self._cee_hook is None:
            self._cee_hook = ConsistencyEvaluationEngineIntegrationPoint(
                settings=self._evidence_analysis_settings(),
            )
        return self._cee_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_ANALYZER_COUNT

    def initialize(self) -> None:
        settings = self._evidence_analysis_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = EvidenceAnalysisExecutor(self._registry)
        self._cee_hook = ConsistencyEvaluationEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def analyze(self, request: EvidenceAnalysisRequest) -> EvidenceAnalysisResult:
        settings = self._evidence_analysis_settings()
        catalog_view = self._gateway.validate(request.definitive_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        cee_status = self.consistency_evaluation_integration.prepare_for_future_consistency_evaluation(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"consistency_evaluation_engine_status={cee_status['status']}",
        )
        return EvidenceAnalysisResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            evidence_records_count=result.evidence_records_count,
            missing_evidence_records_count=result.missing_evidence_records_count,
            definitive_catalog_preserved=result.definitive_catalog_preserved,
            source_data_preserved=result.source_data_preserved,
            analyzers_executed=result.analyzers_executed,
            incidents=result.incidents,
            technical_observations=observations,
        )

    def extend(self, analyzer: EvidenceAnalyzerPort) -> None:
        """Incorpora un nuevo analizador mediante extensión sin modificar el núcleo."""
        self._registry.register(analyzer)

    def _evidence_analysis_settings(self) -> EvidenceAnalysisEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.intelligent_analysis().evidence_analysis_engine
        return EvidenceAnalysisEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._evidence_analysis_settings()
        return {
            "initialized": self._initialized,
            "analyzers_count": self._registry.count(),
            "analyzers": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "consistency_evaluation_integration": self.consistency_evaluation_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "definitive_model_evidence_analyzer_enabled": (
                    settings.definitive_model_evidence_analyzer_enabled
                ),
                "detect_missing_categories": settings.detect_missing_categories,
                "detect_missing_cell_values": settings.detect_missing_cell_values,
                "evidence_id_prefix": settings.evidence_id_prefix,
                "consistency_evaluation_engine_prepared": (
                    settings.consistency_evaluation_engine_prepared
                ),
            },
        }
