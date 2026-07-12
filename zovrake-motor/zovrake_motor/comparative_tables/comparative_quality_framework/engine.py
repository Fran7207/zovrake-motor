"""Motor central del Comparative Quality Framework (CQF)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.comparative_quality_framework.executor import (
    ComparativeQualityExecutor,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.gateway import (
    ComparativeQualityInputGateway,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.integration_hooks import (
    ModuleCertificationIntegrationPoint,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidationRequest,
    ComparativeQualityValidationResult,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.port import (
    ComparativeQualityValidatorPort,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.registry import (
    ComparativeQualityValidatorRegistry,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.report_store import (
    ComparativeQualityReportStore,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeQualityFrameworkSettings,
)

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeQualityFrameworkCore:
    """
    Comparative Quality Framework (CQF).

    Audita calidad arquitectónica, funcional y estructural del PM6.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_VALIDATOR_COUNT = 6

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ComparativeQualityValidatorRegistry | None = None,
        gateway: ComparativeQualityInputGateway | None = None,
        report_store: ComparativeQualityReportStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ComparativeQualityValidatorRegistry()
        self._gateway = gateway or ComparativeQualityInputGateway()
        self._report_store = report_store or ComparativeQualityReportStore()
        self._executor: ComparativeQualityExecutor | None = None
        self._certification_hook: ModuleCertificationIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ComparativeQualityValidatorRegistry:
        return self._registry

    @property
    def report_store(self) -> ComparativeQualityReportStore:
        return self._report_store

    @property
    def executor(self) -> ComparativeQualityExecutor:
        if self._executor is None:
            self._executor = ComparativeQualityExecutor(self._registry)
        return self._executor

    @property
    def certification_integration(self) -> ModuleCertificationIntegrationPoint:
        if self._certification_hook is None:
            self._certification_hook = ModuleCertificationIntegrationPoint(
                settings=self._quality_settings(),
            )
        return self._certification_hook

    def is_ready(self) -> bool:
        return (
            self._initialized
            and self._registry.count() >= self.EXPECTED_VALIDATOR_COUNT
        )

    def initialize(self) -> None:
        settings = self._quality_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ComparativeQualityExecutor(self._registry)
        self._certification_hook = ModuleCertificationIntegrationPoint(
            settings=settings,
        )
        self._initialized = True

    def audit(
        self,
        request: ComparativeQualityValidationRequest,
    ) -> ComparativeQualityValidationResult:
        settings = self._quality_settings()
        input_view = self._gateway.validate(
            request.definitive_catalog,
            request.validation_report,
            pipeline_snapshot=request.pipeline_snapshot,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._report_store.save(result.report)

        certification_status = self.certification_integration.prepare_for_future_certification(
            result.report,
        )
        observations = (
            *result.technical_observations,
            f"module_certification_status={certification_status['status']}",
        )
        return ComparativeQualityValidationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            report=result.report,
            status=result.status,
            definitive_catalog_preserved=result.definitive_catalog_preserved,
            validation_report_preserved=result.validation_report_preserved,
            domain_model_preserved=result.domain_model_preserved,
            validators_executed=result.validators_executed,
            technical_observations=observations,
        )

    def extend(self, validator: ComparativeQualityValidatorPort) -> None:
        """Incorpora un nuevo auditor mediante extensión sin modificar el núcleo."""
        self._registry.register(validator)

    def _quality_settings(self) -> ComparativeQualityFrameworkSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().comparative_quality_framework
        return ComparativeQualityFrameworkSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._quality_settings()
        return {
            "initialized": self._initialized,
            "validators_count": self._registry.count(),
            "validators": self._registry.snapshot(),
            "report_entries_count": self._report_store.count(),
            "gateway": self._gateway.snapshot(),
            "certification_integration": self.certification_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "architectural_compliance_validator_enabled": (
                    settings.architectural_compliance_validator_enabled
                ),
                "definitive_model_consistency_validator_enabled": (
                    settings.definitive_model_consistency_validator_enabled
                ),
                "validation_report_integrity_validator_enabled": (
                    settings.validation_report_integrity_validator_enabled
                ),
                "identifier_uniqueness_validator_enabled": (
                    settings.identifier_uniqueness_validator_enabled
                ),
                "traceability_chain_validator_enabled": (
                    settings.traceability_chain_validator_enabled
                ),
                "pipeline_flow_validator_enabled": settings.pipeline_flow_validator_enabled,
                "module_certification_prepared": settings.module_certification_prepared,
            },
        }
