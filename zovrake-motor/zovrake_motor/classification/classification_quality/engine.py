"""Motor central del Classification Quality Framework (CQF)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.classification_quality.catalog import ClassificationQualityReportStore
from zovrake_motor.classification.classification_quality.executor import ClassificationQualityExecutor
from zovrake_motor.classification.classification_quality.gateway import ComparativeDomainModelCatalogGateway
from zovrake_motor.classification.classification_quality.models import (
    ClassificationQualityValidationRequest,
    ClassificationQualityValidationResult,
)
from zovrake_motor.classification.classification_quality.port import QualityValidatorPort
from zovrake_motor.classification.classification_quality.registry import QualityValidatorRegistry
from zovrake_motor.config.categories.classification import ClassificationQualityFrameworkSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ClassificationQualityFrameworkEngine:
    """
    Classification Quality Framework (CQF).

    Valida consistencia, integridad, unicidad y trazabilidad de la clasificación.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_VALIDATOR_COUNT = 5

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: QualityValidatorRegistry | None = None,
        gateway: ComparativeDomainModelCatalogGateway | None = None,
        report_store: ClassificationQualityReportStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or QualityValidatorRegistry()
        self._gateway = gateway or ComparativeDomainModelCatalogGateway()
        self._report_store = report_store or ClassificationQualityReportStore()
        self._executor: ClassificationQualityExecutor | None = None
        self._initialized = False

    @property
    def registry(self) -> QualityValidatorRegistry:
        return self._registry

    @property
    def report_store(self) -> ClassificationQualityReportStore:
        return self._report_store

    @property
    def executor(self) -> ClassificationQualityExecutor:
        if self._executor is None:
            self._executor = ClassificationQualityExecutor(self._registry)
        return self._executor

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_VALIDATOR_COUNT

    def initialize(self) -> None:
        settings = self._classification_quality_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ClassificationQualityExecutor(self._registry)
        self._initialized = True

    def validate(
        self,
        request: ClassificationQualityValidationRequest,
    ) -> ClassificationQualityValidationResult:
        settings = self._classification_quality_settings()
        catalog_view = self._gateway.validate(
            request.comparative_domain_model_catalog,
            pipeline_snapshot=request.pipeline_snapshot,
        )
        result = self.executor.execute(catalog_view, settings=settings)
        self._report_store.save(result.report)
        return result

    def extend(self, validator: QualityValidatorPort) -> None:
        self._registry.register(validator)

    def _classification_quality_settings(self) -> ClassificationQualityFrameworkSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().classification_quality_framework
        return ClassificationQualityFrameworkSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._classification_quality_settings()
        return {
            "initialized": self._initialized,
            "validators_count": self._registry.count(),
            "validators": self._registry.snapshot(),
            "report_entries_count": self._report_store.count(),
            "gateway": self._gateway.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "model_consistency_validator_enabled": settings.model_consistency_validator_enabled,
                "data_integrity_validator_enabled": settings.data_integrity_validator_enabled,
                "identifier_uniqueness_validator_enabled": settings.identifier_uniqueness_validator_enabled,
                "traceability_chain_validator_enabled": settings.traceability_chain_validator_enabled,
                "pipeline_flow_validator_enabled": settings.pipeline_flow_validator_enabled,
                "certification_prepared": settings.certification_prepared,
            },
        }
