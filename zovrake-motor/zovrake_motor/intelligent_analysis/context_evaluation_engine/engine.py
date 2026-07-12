"""Motor central del Context Evaluation Engine (CxEE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.context_evaluation_engine.catalog_store import (
    ContextEvaluationCatalogStore,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.executor import (
    ContextEvaluationExecutor,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.gateway import (
    ContextEvaluationInputGateway,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.integration_hooks import (
    ExplanationGenerationEngineIntegrationPoint,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationRequest,
    ContextEvaluationResult,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.port import ContextEvaluatorPort
from zovrake_motor.intelligent_analysis.context_evaluation_engine.registry import (
    ContextEvaluatorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ContextEvaluationEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ContextEvaluationBuilderEngine:
    """
    Context Evaluation Engine (CxEE).

    Evalúa cómo el contexto del requerimiento influye en la interpretación de evidencias.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_EVALUATOR_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ContextEvaluatorRegistry | None = None,
        gateway: ContextEvaluationInputGateway | None = None,
        catalog_store: ContextEvaluationCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ContextEvaluatorRegistry()
        self._gateway = gateway or ContextEvaluationInputGateway()
        self._catalog_store = catalog_store or ContextEvaluationCatalogStore()
        self._executor: ContextEvaluationExecutor | None = None
        self._ege_hook: ExplanationGenerationEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ContextEvaluatorRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ContextEvaluationCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ContextEvaluationExecutor:
        if self._executor is None:
            self._executor = ContextEvaluationExecutor(self._registry)
        return self._executor

    @property
    def explanation_generation_integration(self) -> ExplanationGenerationEngineIntegrationPoint:
        if self._ege_hook is None:
            self._ege_hook = ExplanationGenerationEngineIntegrationPoint(
                settings=self._context_evaluation_settings(),
            )
        return self._ege_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_EVALUATOR_COUNT

    def initialize(self) -> None:
        settings = self._context_evaluation_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ContextEvaluationExecutor(self._registry)
        self._ege_hook = ExplanationGenerationEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def evaluate(self, request: ContextEvaluationRequest) -> ContextEvaluationResult:
        settings = self._context_evaluation_settings()
        input_view = self._gateway.validate(
            evidence_catalog=request.evidence_catalog,
            consistency_catalog=request.consistency_catalog,
            risk_catalog=request.risk_catalog,
            definitive_catalog=request.definitive_catalog,
            requirement_context=request.requirement_context,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        ege_status = self.explanation_generation_integration.prepare_for_future_explanation_generation(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"explanation_generation_engine_status={ege_status['status']}",
        )
        return ContextEvaluationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            associations_count=result.associations_count,
            contextual_gaps_count=result.contextual_gaps_count,
            evidence_catalog_preserved=result.evidence_catalog_preserved,
            consistency_catalog_preserved=result.consistency_catalog_preserved,
            risk_catalog_preserved=result.risk_catalog_preserved,
            definitive_catalog_preserved=result.definitive_catalog_preserved,
            requirement_context_preserved=result.requirement_context_preserved,
            source_data_preserved=result.source_data_preserved,
            evaluators_executed=result.evaluators_executed,
            incidents=result.incidents,
            technical_observations=observations,
        )

    def extend(self, evaluator: ContextEvaluatorPort) -> None:
        """Incorpora un nuevo evaluador mediante extensión sin modificar el núcleo."""
        self._registry.register(evaluator)

    def _context_evaluation_settings(self) -> ContextEvaluationEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.intelligent_analysis().context_evaluation_engine
        return ContextEvaluationEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._context_evaluation_settings()
        return {
            "initialized": self._initialized,
            "evaluators_count": self._registry.count(),
            "evaluators": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "explanation_generation_integration": self.explanation_generation_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_input_immutability": settings.preserve_input_immutability,
                "organized_context_evaluator_enabled": settings.organized_context_evaluator_enabled,
                "detect_commercial_alignment": settings.detect_commercial_alignment,
                "detect_technical_alignment": settings.detect_technical_alignment,
                "detect_context_gaps": settings.detect_context_gaps,
                "detect_context_limitations": settings.detect_context_limitations,
                "detect_quotation_alignment": settings.detect_quotation_alignment,
                "association_id_prefix": settings.association_id_prefix,
                "explanation_generation_engine_prepared": (
                    settings.explanation_generation_engine_prepared
                ),
            },
        }
