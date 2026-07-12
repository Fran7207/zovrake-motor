"""Motor central del Reasoning Result Builder (RRB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.reasoning_result_builder.catalog_store import (
    ReasoningResultCatalogStore,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.executor import (
    ReasoningResultBuildExecutor,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.gateway import (
    ReasoningResultInputGateway,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.integration_hooks import (
    IntegrationCertificationFrameworkIntegrationPoint,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    ReasoningResultBuildRequest,
    ReasoningResultBuildResult,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.port import ReasoningResultBuilderPort
from zovrake_motor.intelligent_analysis.reasoning_result_builder.registry import (
    ReasoningResultBuilderRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ReasoningResultBuilderSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ReasoningResultBuilderEngine:
    """
    Reasoning Result Builder (RRB).

    Construye el Resultado del Análisis Inteligente — único contrato de salida del PM7.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_BUILDER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ReasoningResultBuilderRegistry | None = None,
        gateway: ReasoningResultInputGateway | None = None,
        catalog_store: ReasoningResultCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ReasoningResultBuilderRegistry()
        self._gateway = gateway or ReasoningResultInputGateway()
        self._catalog_store = catalog_store or ReasoningResultCatalogStore()
        self._executor: ReasoningResultBuildExecutor | None = None
        self._icf_hook: IntegrationCertificationFrameworkIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ReasoningResultBuilderRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ReasoningResultCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ReasoningResultBuildExecutor:
        if self._executor is None:
            self._executor = ReasoningResultBuildExecutor(self._registry)
        return self._executor

    @property
    def integration_certification_integration(self) -> IntegrationCertificationFrameworkIntegrationPoint:
        if self._icf_hook is None:
            self._icf_hook = IntegrationCertificationFrameworkIntegrationPoint(
                settings=self._reasoning_result_builder_settings(),
            )
        return self._icf_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        settings = self._reasoning_result_builder_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ReasoningResultBuildExecutor(self._registry)
        self._icf_hook = IntegrationCertificationFrameworkIntegrationPoint(settings=settings)
        self._initialized = True

    def build(self, request: ReasoningResultBuildRequest) -> ReasoningResultBuildResult:
        settings = self._reasoning_result_builder_settings()
        input_view = self._gateway.validate(
            evidence_catalog=request.evidence_catalog,
            consistency_catalog=request.consistency_catalog,
            risk_catalog=request.risk_catalog,
            context_catalog=request.context_catalog,
            explanation_catalog=request.explanation_catalog,
            recommendation_catalog=request.recommendation_catalog,
            definitive_catalog=request.definitive_catalog,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        icf_status = self.integration_certification_integration.prepare_for_future_certification(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"integration_certification_framework_status={icf_status['status']}",
        )
        return ReasoningResultBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            results_count=result.results_count,
            evidence_catalog_preserved=result.evidence_catalog_preserved,
            consistency_catalog_preserved=result.consistency_catalog_preserved,
            risk_catalog_preserved=result.risk_catalog_preserved,
            context_catalog_preserved=result.context_catalog_preserved,
            explanation_catalog_preserved=result.explanation_catalog_preserved,
            recommendation_catalog_preserved=result.recommendation_catalog_preserved,
            definitive_catalog_preserved=result.definitive_catalog_preserved,
            source_data_preserved=result.source_data_preserved,
            builders_executed=result.builders_executed,
            incidents=result.incidents,
            technical_observations=observations,
        )

    def extend(self, builder: ReasoningResultBuilderPort) -> None:
        """Incorpora un nuevo constructor mediante extensión sin modificar el núcleo."""
        self._registry.register(builder)

    def _reasoning_result_builder_settings(self) -> ReasoningResultBuilderSettings:
        if self._config_provider is not None:
            return self._config_provider.intelligent_analysis().reasoning_result_builder
        return ReasoningResultBuilderSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._reasoning_result_builder_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "integration_certification_integration": self.integration_certification_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_input_immutability": settings.preserve_input_immutability,
                "organized_result_builder_enabled": settings.organized_result_builder_enabled,
                "result_id_prefix": settings.result_id_prefix,
                "integration_certification_framework_prepared": (
                    settings.integration_certification_framework_prepared
                ),
            },
        }
