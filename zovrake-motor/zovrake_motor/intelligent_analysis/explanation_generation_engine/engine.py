"""Motor central del Explanation Generation Engine (EGE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.explanation_generation_engine.catalog_store import (
    ExplanationGenerationCatalogStore,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.executor import (
    ExplanationGenerationExecutor,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ExplanationGenerationInputGateway,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.integration_hooks import (
    ConclusionGenerationEngineIntegrationPoint,
    RecommendationGenerationEngineIntegrationPoint,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationRequest,
    ExplanationGenerationResult,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.port import (
    ExplanationGeneratorPort,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.registry import (
    ExplanationGeneratorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ExplanationGenerationEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ExplanationGenerationBuilderEngine:
    """
    Explanation Generation Engine (EGE).

    Transforma la información de motores anteriores en explicaciones estructuradas
    y trazables. Ningún otro componente realiza esta función.
    """

    EXPECTED_GENERATOR_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ExplanationGeneratorRegistry | None = None,
        gateway: ExplanationGenerationInputGateway | None = None,
        catalog_store: ExplanationGenerationCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ExplanationGeneratorRegistry()
        self._gateway = gateway or ExplanationGenerationInputGateway()
        self._catalog_store = catalog_store or ExplanationGenerationCatalogStore()
        self._executor: ExplanationGenerationExecutor | None = None
        self._cge_hook: ConclusionGenerationEngineIntegrationPoint | None = None
        self._rge_hook: RecommendationGenerationEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ExplanationGeneratorRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ExplanationGenerationCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ExplanationGenerationExecutor:
        if self._executor is None:
            self._executor = ExplanationGenerationExecutor(self._registry)
        return self._executor

    @property
    def conclusion_generation_integration(self) -> ConclusionGenerationEngineIntegrationPoint:
        if self._cge_hook is None:
            self._cge_hook = ConclusionGenerationEngineIntegrationPoint(
                settings=self._explanation_generation_settings(),
            )
        return self._cge_hook

    @property
    def recommendation_generation_integration(self) -> RecommendationGenerationEngineIntegrationPoint:
        if self._rge_hook is None:
            self._rge_hook = RecommendationGenerationEngineIntegrationPoint(
                settings=self._explanation_generation_settings(),
            )
        return self._rge_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_GENERATOR_COUNT

    def initialize(self) -> None:
        settings = self._explanation_generation_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ExplanationGenerationExecutor(self._registry)
        self._cge_hook = ConclusionGenerationEngineIntegrationPoint(settings=settings)
        self._rge_hook = RecommendationGenerationEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def generate(self, request: ExplanationGenerationRequest) -> ExplanationGenerationResult:
        settings = self._explanation_generation_settings()
        input_view = self._gateway.validate(
            evidence_catalog=request.evidence_catalog,
            consistency_catalog=request.consistency_catalog,
            risk_catalog=request.risk_catalog,
            context_catalog=request.context_catalog,
            definitive_catalog=request.definitive_catalog,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        cge_status = self.conclusion_generation_integration.prepare_for_future_conclusion_generation(
            result.catalog,
        )

        rge_status = self.recommendation_generation_integration.prepare_for_future_recommendation_generation(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"conclusion_generation_engine_status={cge_status['status']}",
            f"recommendation_generation_engine_status={rge_status['status']}",
        )
        return ExplanationGenerationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            segments_count=result.segments_count,
            evidence_catalog_preserved=result.evidence_catalog_preserved,
            consistency_catalog_preserved=result.consistency_catalog_preserved,
            risk_catalog_preserved=result.risk_catalog_preserved,
            context_catalog_preserved=result.context_catalog_preserved,
            definitive_catalog_preserved=result.definitive_catalog_preserved,
            source_data_preserved=result.source_data_preserved,
            generators_executed=result.generators_executed,
            incidents=result.incidents,
            technical_observations=observations,
        )

    def extend(self, generator: ExplanationGeneratorPort) -> None:
        """Incorpora un nuevo generador mediante extensión sin modificar el núcleo."""
        self._registry.register(generator)

    def _explanation_generation_settings(self) -> ExplanationGenerationEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.intelligent_analysis().explanation_generation_engine
        return ExplanationGenerationEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._explanation_generation_settings()
        return {
            "initialized": self._initialized,
            "generators_count": self._registry.count(),
            "generators": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "conclusion_generation_integration": self.conclusion_generation_integration.snapshot(),
            "recommendation_generation_integration": self.recommendation_generation_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_input_immutability": settings.preserve_input_immutability,
                "organized_explanation_generator_enabled": (
                    settings.organized_explanation_generator_enabled
                ),
                "generate_summary_sections": settings.generate_summary_sections,
                "generate_evidence_sections": settings.generate_evidence_sections,
                "generate_strength_sections": settings.generate_strength_sections,
                "generate_weakness_sections": settings.generate_weakness_sections,
                "generate_risk_sections": settings.generate_risk_sections,
                "generate_consistency_sections": settings.generate_consistency_sections,
                "generate_context_sections": settings.generate_context_sections,
                "generate_missing_information_sections": (
                    settings.generate_missing_information_sections
                ),
                "generate_limitation_sections": settings.generate_limitation_sections,
                "segment_id_prefix": settings.segment_id_prefix,
                "recommendation_generation_engine_prepared": (
                    settings.recommendation_generation_engine_prepared
                ),
                "conclusion_generation_engine_prepared": (
                    settings.conclusion_generation_engine_prepared
                ),
            },
        }
