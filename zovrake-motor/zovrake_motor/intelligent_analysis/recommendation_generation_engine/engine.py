"""Motor central del Recommendation Generation Engine (RGE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.catalog_store import (
    RecommendationGenerationCatalogStore,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.executor import (
    RecommendationGenerationExecutor,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.gateway import (
    RecommendationGenerationInputGateway,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.integration_hooks import (
    ReasoningResultBuilderIntegrationPoint,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationRequest,
    RecommendationGenerationResult,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.port import (
    RecommendationGeneratorPort,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.registry import (
    RecommendationGeneratorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import RecommendationGenerationEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class RecommendationGenerationBuilderEngine:
    """
    Recommendation Generation Engine (RGE).

    Genera recomendaciones fundamentadas como apoyo a la decisión.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_GENERATOR_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: RecommendationGeneratorRegistry | None = None,
        gateway: RecommendationGenerationInputGateway | None = None,
        catalog_store: RecommendationGenerationCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or RecommendationGeneratorRegistry()
        self._gateway = gateway or RecommendationGenerationInputGateway()
        self._catalog_store = catalog_store or RecommendationGenerationCatalogStore()
        self._executor: RecommendationGenerationExecutor | None = None
        self._rrb_hook: ReasoningResultBuilderIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> RecommendationGeneratorRegistry:
        return self._registry

    @property
    def catalog_store(self) -> RecommendationGenerationCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> RecommendationGenerationExecutor:
        if self._executor is None:
            self._executor = RecommendationGenerationExecutor(self._registry)
        return self._executor

    @property
    def reasoning_result_builder_integration(self) -> ReasoningResultBuilderIntegrationPoint:
        if self._rrb_hook is None:
            self._rrb_hook = ReasoningResultBuilderIntegrationPoint(
                settings=self._recommendation_generation_settings(),
            )
        return self._rrb_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_GENERATOR_COUNT

    def initialize(self) -> None:
        settings = self._recommendation_generation_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = RecommendationGenerationExecutor(self._registry)
        self._rrb_hook = ReasoningResultBuilderIntegrationPoint(settings=settings)
        self._initialized = True

    def generate(self, request: RecommendationGenerationRequest) -> RecommendationGenerationResult:
        settings = self._recommendation_generation_settings()
        input_view = self._gateway.validate(
            evidence_catalog=request.evidence_catalog,
            consistency_catalog=request.consistency_catalog,
            risk_catalog=request.risk_catalog,
            context_catalog=request.context_catalog,
            explanation_catalog=request.explanation_catalog,
            definitive_catalog=request.definitive_catalog,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        rrb_status = self.reasoning_result_builder_integration.prepare_for_future_result_building(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"reasoning_result_builder_status={rrb_status['status']}",
        )
        return RecommendationGenerationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            recommendations_count=result.recommendations_count,
            evidence_catalog_preserved=result.evidence_catalog_preserved,
            consistency_catalog_preserved=result.consistency_catalog_preserved,
            risk_catalog_preserved=result.risk_catalog_preserved,
            context_catalog_preserved=result.context_catalog_preserved,
            explanation_catalog_preserved=result.explanation_catalog_preserved,
            definitive_catalog_preserved=result.definitive_catalog_preserved,
            source_data_preserved=result.source_data_preserved,
            generators_executed=result.generators_executed,
            incidents=result.incidents,
            technical_observations=observations,
        )

    def extend(self, generator: RecommendationGeneratorPort) -> None:
        """Incorpora un nuevo generador mediante extensión sin modificar el núcleo."""
        self._registry.register(generator)

    def _recommendation_generation_settings(self) -> RecommendationGenerationEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.intelligent_analysis().recommendation_generation_engine
        return RecommendationGenerationEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._recommendation_generation_settings()
        return {
            "initialized": self._initialized,
            "generators_count": self._registry.count(),
            "generators": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "reasoning_result_builder_integration": self.reasoning_result_builder_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_input_immutability": settings.preserve_input_immutability,
                "organized_recommendation_generator_enabled": (
                    settings.organized_recommendation_generator_enabled
                ),
                "min_evidence_for_recommendation": settings.min_evidence_for_recommendation,
                "clear_winner_score_gap": settings.clear_winner_score_gap,
                "equivalence_score_threshold": settings.equivalence_score_threshold,
                "reasoning_result_builder_prepared": settings.reasoning_result_builder_prepared,
            },
        }
