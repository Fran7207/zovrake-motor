"""Motor central del Comparative Validation Framework (CVF)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.comparative_validation_framework.executor import (
    ComparativeModelValidationExecutor,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.gateway import (
    ModelValidationInputGateway,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.integration_hooks import (
    ComparativeQualityFrameworkIntegrationPoint,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationRequest,
    ComparativeModelValidationResult,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.port import (
    ValidationValidatorPort,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.registry import (
    ValidationValidatorRegistry,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.report_store import (
    ComparativeValidationReportStore,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeValidationFrameworkSettings,
)

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeValidationFrameworkCore:
    """
    Comparative Validation Framework (CVF).

    Valida integridad, consistencia, completitud y trazabilidad del
    Modelo Comparativo Definitivo generado por el CMB.
    """

    EXPECTED_VALIDATOR_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ValidationValidatorRegistry | None = None,
        gateway: ModelValidationInputGateway | None = None,
        report_store: ComparativeValidationReportStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ValidationValidatorRegistry()
        self._gateway = gateway or ModelValidationInputGateway()
        self._report_store = report_store or ComparativeValidationReportStore()
        self._executor: ComparativeModelValidationExecutor | None = None
        self._cqf_hook: ComparativeQualityFrameworkIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ValidationValidatorRegistry:
        return self._registry

    @property
    def report_store(self) -> ComparativeValidationReportStore:
        return self._report_store

    @property
    def executor(self) -> ComparativeModelValidationExecutor:
        if self._executor is None:
            self._executor = ComparativeModelValidationExecutor(self._registry)
        return self._executor

    @property
    def quality_framework_integration(self) -> ComparativeQualityFrameworkIntegrationPoint:
        if self._cqf_hook is None:
            self._cqf_hook = ComparativeQualityFrameworkIntegrationPoint(
                settings=self._validation_settings(),
            )
        return self._cqf_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_VALIDATOR_COUNT

    def initialize(self) -> None:
        settings = self._validation_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ComparativeModelValidationExecutor(self._registry)
        self._cqf_hook = ComparativeQualityFrameworkIntegrationPoint(settings=settings)
        self._initialized = True

    def validate(
        self,
        request: ComparativeModelValidationRequest,
    ) -> ComparativeModelValidationResult:
        settings = self._validation_settings()
        input_view = self._gateway.validate(request.definitive_catalog)
        result = self.executor.execute(input_view, settings=settings)
        self._report_store.save(result.report)

        cqf_status = self.quality_framework_integration.prepare_for_future_quality_audit(
            result.report,
        )
        observations = (
            *result.technical_observations,
            f"comparative_quality_framework_status={cqf_status['status']}",
        )
        return ComparativeModelValidationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            report=result.report,
            status=result.status,
            findings_count=result.findings_count,
            error_count=result.error_count,
            warning_count=result.warning_count,
            definitive_catalog_preserved=result.definitive_catalog_preserved,
            domain_model_preserved=result.domain_model_preserved,
            validators_executed=result.validators_executed,
            technical_observations=observations,
        )

    def extend(self, validator: ValidationValidatorPort) -> None:
        """Incorpora un nuevo validador mediante extensión sin modificar el núcleo."""
        self._registry.register(validator)

    def _validation_settings(self) -> ComparativeValidationFrameworkSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().comparative_validation_framework
        return ComparativeValidationFrameworkSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._validation_settings()
        return {
            "initialized": self._initialized,
            "validators_count": self._registry.count(),
            "validators": self._registry.snapshot(),
            "report_entries_count": self._report_store.count(),
            "gateway": self._gateway.snapshot(),
            "quality_framework_integration": self.quality_framework_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "definitive_comparative_model_validator_enabled": (
                    settings.definitive_comparative_model_validator_enabled
                ),
                "finding_id_prefix": settings.finding_id_prefix,
                "finding_id_padding": settings.finding_id_padding,
                "max_errors_before_invalid": settings.max_errors_before_invalid,
                "comparative_quality_framework_prepared": (
                    settings.comparative_quality_framework_prepared
                ),
            },
        }
